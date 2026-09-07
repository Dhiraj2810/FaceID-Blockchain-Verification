import sys, os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import requests
import cv2
import numpy as np

out = []
img_path = str(BASE_DIR / "input" / "temp_url_input.jpg")
path = Path(img_path)

out.append(f"Original file size: {path.stat().st_size} bytes")

# Resize to max 800px & compress to JPEG
img = cv2.imread(img_path)
h, w = img.shape[:2]
scale = 800.0 / max(h, w)
resized = cv2.resize(img, (int(w*scale), int(h*scale)))
_, buf = cv2.imencode(".jpg", resized, [cv2.IMWRITE_JPEG_QUALITY, 85])
compressed_bytes = buf.tobytes()
out.append(f"Compressed image size: {len(compressed_bytes)} bytes")

# Upload to tmpfiles.org
res2 = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": ("elon_800.jpg", compressed_bytes, "image/jpeg")}, timeout=15)
out.append(f"tmpfiles upload status: {res2.status_code}")

if res2.status_code == 200:
    data = res2.json()
    raw_url = data.get("data", {}).get("url", "").replace("tmpfiles.org/", "tmpfiles.org/dl/")
    out.append(f"Direct image URL: {raw_url}")

    # Query SerpApi
    from app.config import settings
    params = {
        "engine": "google_lens",
        "url": raw_url,
        "api_key": settings.SERPAPI_API_KEY
    }
    s_res = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
    out.append(f"SerpApi HTTP Status: {s_res.status_code}")
    if s_res.status_code == 200:
        s_data = s_res.json()
        out.append(f"SerpApi Keys: {list(s_data.keys())}")
        if "visual_matches" in s_data:
            out.append(f"SUCCESS: {len(s_data['visual_matches'])} visual matches found!")
            for m in s_data["visual_matches"][:5]:
                out.append(f"  Match: {m.get('title')} -> {m.get('link')}")

with open(BASE_DIR / "search_test_out.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("DONE SEARCH TEST")
