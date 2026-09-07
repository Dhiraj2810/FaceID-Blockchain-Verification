import json
import time
from pathlib import Path
from typing import List, Dict, Any
import requests
from app.config import settings
from app.evidence.models import CandidateResult
from app.search.base import BaseReverseImageSearcher


class SerpApiLensSearcher(BaseReverseImageSearcher):
    """
    Reverse Image Search provider using SerpApi Google Lens Engine.
    Executes genuine runtime GET requests to SerpApi Google Lens.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.SERPAPI_API_KEY
        self.api_url = "https://serpapi.com/search.json"

    def _get_public_image_url(self, image_path: str) -> str:
        """
        Ensures the image is accessible via HTTP/HTTPS URL as required by SerpApi Google Lens.
        Compresses image to web-optimized JPEG (<1MB) and uploads to reliable public CDN (Catbox.moe / tmpfiles.org).
        """
        clean_path = str(image_path).replace("\\", "/")
        if clean_path.startswith("http://") or clean_path.startswith("https://"):
            return clean_path

        path = Path(image_path)
        if not path.is_file():
            raise FileNotFoundError(f"Input image for search not found: {image_path}")

        # Web-optimize image (max side 640px, JPEG quality 80 for instant upload)
        try:
            import cv2
            img = cv2.imread(str(path))
            if img is not None and img.size > 0:
                h, w = img.shape[:2]
                max_d = max(h, w)
                if max_d > 640:
                    scale = 640.0 / max_d
                    img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
                _, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])
                file_bytes = buf.tobytes()
            else:
                with open(path, "rb") as f:
                    file_bytes = f.read()
        except Exception:
            with open(path, "rb") as f:
                file_bytes = f.read()

        # Primary Upload Provider: Catbox.moe (Fast, Google Lens crawler friendly)
        try:
            res_c = requests.post(
                "https://catbox.moe/user/api.php",
                data={"reqtype": "fileupload"},
                files={"fileToUpload": (path.name or "face.jpg", file_bytes, "image/jpeg")},
                timeout=6
            )
            if res_c.status_code == 200 and res_c.text.startswith("http"):
                public_url = res_c.text.strip()
                print(f"      [+] Public CDN Image Hosted (Catbox): {public_url}")
                return public_url
        except Exception as ex_c:
            print(f"[SerpApiLens] Catbox upload notice: {ex_c}")

        # Secondary Fallback: tmpfiles.org
        try:
            res_t = requests.post(
                "https://tmpfiles.org/api/v1/upload",
                files={"file": (path.name or "face.jpg", file_bytes, "image/jpeg")},
                timeout=6
            )
            if res_t.status_code == 200:
                data = res_t.json()
                raw_url = data.get("data", {}).get("url", "")
                if raw_url and "tmpfiles.org/" in raw_url:
                    direct_url = raw_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
                    print(f"      [+] Public CDN Image Hosted (tmpfiles): {direct_url}")
                    return direct_url
        except Exception as ex_t:
            print(f"[SerpApiLens] tmpfiles upload notice: {ex_t}")


        raise RuntimeError(f"Could not prepare public image URL for input file: {image_path}")

    def search(self, image_path: str) -> List[CandidateResult]:
        if not self.api_key or self.api_key.startswith("your_serpapi_key"):
            raise ValueError(
                "❌ SERPAPI_API_KEY is not configured.\n"
                "Real reverse-image search cannot be performed. Please set SERPAPI_API_KEY in your .env file."
            )

        target_url = self._get_public_image_url(image_path)

        try:
            params = {
                "engine": "google_lens",
                "url": target_url,
                "api_key": self.api_key
            }
            response = requests.get(
                self.api_url,
                params=params,
                timeout=settings.REQUEST_TIMEOUT
            )

            if response.status_code != 200:
                raise RuntimeError(
                    f"SerpApi Google Lens API request failed with HTTP {response.status_code}: {response.text[:200]}"
                )

            data = response.json()
            if "error" in data:
                raise RuntimeError(f"SerpApi returned error: {data['error']}")

            self._save_raw_response(data)
            candidates = self.parse_response(data)
            return candidates

        except requests.RequestException as req_err:
            raise RuntimeError(f"Network timeout / connection error calling SerpApi Google Lens: {req_err}")

    def parse_response(self, data: dict) -> List[CandidateResult]:
        """
        Parses raw SerpApi Google Lens JSON response into CandidateResult objects.
        Scans visual_matches, exact_matches, related_content, organic_results, images_results, and knowledge_graph.
        """
        # Safely log top-level keys without revealing sensitive params
        top_keys = [k for k in data.keys() if k not in ("search_parameters", "search_metadata")]
        print(f"      SerpApi Response Keys: {', '.join(top_keys)}")

        candidates = []
        seen_urls = set()

        def extract_item(item: dict, match_type: str = "Google Lens"):
            if not isinstance(item, dict):
                return

            url = item.get("link") or item.get("source") or item.get("page_url") or item.get("url")
            if not url or url in seen_urls:
                return

            title = item.get("title") or item.get("snippet") or item.get("source_name") or f"Discovered Evidence ({match_type})"
            thumbnail_url = item.get("thumbnail") or item.get("image") or item.get("original")

            seen_urls.add(url)
            candidates.append(
                CandidateResult(
                    title=title,
                    url=url,
                    thumbnail_url=thumbnail_url,
                    source=f"Google Lens ({match_type})"
                )
            )

        # 1. Extract visual_matches
        visual_matches = data.get("visual_matches", [])
        if visual_matches:
            print(f"      Found {len(visual_matches)} visual matches")
            for match in visual_matches:
                extract_item(match, "visual")

        # 2. Extract exact_matches
        exact_matches = data.get("exact_matches", [])
        if exact_matches:
            print(f"      Found {len(exact_matches)} exact matches")
            for match in exact_matches:
                extract_item(match, "exact")

        # 3. Extract related_content
        related_content = data.get("related_content", [])
        if related_content:
            print(f"      Found {len(related_content)} related content items")
            for match in related_content:
                extract_item(match, "related")

        # 4. Extract organic_results & images_results & inline_images
        organic_results = data.get("organic_results", []) + data.get("images_results", []) + data.get("inline_images", [])
        if organic_results:
            print(f"      Found {len(organic_results)} organic/image results")
            for match in organic_results:
                extract_item(match, "organic")

        # 5. Extract knowledge_graph entries
        kg = data.get("knowledge_graph")
        if kg:
            if isinstance(kg, list):
                for match in kg:
                    extract_item(match, "knowledge_graph")
            elif isinstance(kg, dict):
                for val in kg.values():
                    if isinstance(val, list):
                        for sub in val:
                            extract_item(sub, "knowledge_graph")

        print(f"      Total deduplicated candidate web URLs extracted: {len(candidates)}")
        return candidates[:settings.MAX_CANDIDATES]

    def _save_raw_response(self, data: dict):
        """
        Saves raw API response locally for audit/debugging with API key sanitized.
        """
        sanitized = json.loads(json.dumps(data))
        if "search_parameters" in sanitized and "api_key" in sanitized["search_parameters"]:
            sanitized["search_parameters"]["api_key"] = "REDACTED"

        timestamp = int(time.time())
        output_path = settings.RESULTS_DIR / f"search_raw_{timestamp}.json"
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(sanitized, f, indent=2)
        except Exception as e:
            print(f"[SerpApiLens] Warning: Could not save raw response log: {e}")
