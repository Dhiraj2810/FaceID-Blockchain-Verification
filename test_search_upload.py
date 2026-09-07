import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import requests
import cv2
import numpy as np

img_path = str(BASE_DIR / "input" / "temp_url_input.jpg")
path = Path(img_path)

# Test 1: Upload original raw image (9.3MB) to tmpfiles.org
with open(path, "rb") as f:
    res1 = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": (path.name, f, "image/jpeg")})
print("tmpfiles raw upload:", res1.status_code, res1.json())
raw_url1 = res1.json().get("data", {}).get("url", "").replace("tmpfiles.org/", "tmpfiles.org/dl/")
print("Direct URL 1:", raw_url1)

# Check if direct URL is accessible
h1 = requests.head(raw_url1)
print("Direct URL 1 HTTP HEAD:", h1.status_code, h1.headers.get("content-type"), h1.headers.get("content-length"))

# Test 2: Downscale image to max 1024px & compress to web JPEG (~100KB)
img = cv2.imread(img_path)
h, w = img.shape[:2]
scale = 1024.0 / max(h, w)
resized = cv2.resize(img, (int(w*scale), int(h*scale)))
_, buf = cv2.imencode(".jpg", resized, [cv2.IMWRITE_JPEG_QUALITY, 85])
compressed_bytes = buf.tobytes()
print(f"Compressed size: {len(compressed_bytes)} bytes (original was {path.stat().st_size} bytes)")

res2 = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": ("compressed_elon.jpg", compressed_bytes, "image/jpeg")})
print("tmpfiles compressed upload:", res2.status_code, res2.json())
raw_url2 = res2.json().get("data", {}).get("url", "").replace("tmpfiles.org/", "tmpfiles.org/dl/")
print("Direct URL 2:", raw_url2)

# Test SerpApi Google Lens with direct URL 2
from app.config import settings
params = {
    "engine": "google_lens",
    "url": raw_url2,
    "api_key": settings.SERPAPI_API_KEY
}
s_res = requests.get("https://serpapi.com/search.json", params=params)
print("SerpApi Response Code:", s_res.status_code)
s_data = s_res.json()
print("SerpApi Top Keys:", list(s_data.keys()))
if "visual_matches" in s_data:
    print(f"VISUAL MATCHES FOUND: {len(s_data['visual_matches'])}")
    for m in s_data["visual_matches"][:3]:
        print("  - Title:", m.get("title"))
        print("    Link:", m.get("link"))
elif "exact_matches" in s_data:
    print(f"EXACT MATCHES FOUND: {len(s_data['exact_matches'])}")
