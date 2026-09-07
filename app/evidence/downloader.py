import os
from pathlib import Path
from typing import Optional, Tuple
import cv2
import numpy as np
import requests
from app.config import settings

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp"}


def download_candidate_image(url_or_path: str) -> Tuple[Optional[np.ndarray], Optional[bytes]]:
    """
    Safely downloads or reads a candidate image.
    Validates MIME type, enforces file size limits, and safely decodes via OpenCV.
    Returns:
        (decoded_bgr_image, raw_bytes)
    """
    if not url_or_path:
        return None, None

    # Handle local path (e.g., local candidate files)
    local_path = Path(url_or_path)
    if local_path.is_file():
        try:
            with open(local_path, "rb") as f:
                content = f.read()
            img_np = np.frombuffer(content, dtype=np.uint8)
            img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
            return img, content
        except Exception:
            return None, None

    # Handle Web URL download
    clean_url = str(url_or_path).replace("\\", "/")
    if not (clean_url.startswith("http://") or clean_url.startswith("https://")):
        return None, None

    max_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(
            clean_url,
            headers=headers,
            timeout=5,
            stream=True
        )

        if response.status_code != 200:
            return None, None

        # Check content-length header if provided
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > max_bytes:
            print(f"[Downloader] Skipping candidate: Content-Length ({content_length} bytes) exceeds limit.")
            return None, None

        # Check content-type header
        content_type = response.headers.get("Content-Type", "").split(";")[0].strip().lower()
        if content_type and content_type not in ALLOWED_MIME_TYPES and not content_type.startswith("image/"):
            print(f"[Downloader] Skipping candidate: Unallowed MIME type '{content_type}'.")
            return None, None

        # Stream content up to max_bytes limit
        content = bytearray()
        for chunk in response.iter_content(chunk_size=65536):
            content.extend(chunk)
            if len(content) > max_bytes:
                print("[Downloader] Candidate download aborted: Exceeded maximum allowed image size.")
                return None, None

        raw_bytes = bytes(content)
        img_np = np.frombuffer(raw_bytes, dtype=np.uint8)
        img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
        return img, raw_bytes

    except Exception as e:
        print(f"[Downloader] Failed to fetch image from '{clean_url[:60]}...': {e}")
        return None, None
