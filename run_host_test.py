import requests
import cv2
from pathlib import Path
from app.config import settings

BASE_DIR = Path(__file__).resolve().parent
img_path = str(BASE_DIR / "input" / "temp_url_input.jpg")
img = cv2.imread(img_path)
h, w = img.shape[:2]
scale = 800.0 / max(h, w)
resized = cv2.resize(img, (int(w*scale), int(h*scale)))
_, buf = cv2.imencode(".jpg", resized, [cv2.IMWRITE_JPEG_QUALITY, 85])
compressed_bytes = buf.tobytes()

out = []

# Host 1: Catbox.moe
try:
    c_res = requests.post(
        "https://catbox.moe/user/api.php",
        data={"reqtype": "fileupload"},
        files={"fileToUpload": ("elon.jpg", compressed_bytes, "image/jpeg")},
        timeout=15
    )
    out.append(f"Catbox status: {c_res.status_code}, URL: {c_res.text.strip()}")
    catbox_url = c_res.text.strip()

    # Query SerpApi with catbox URL
    params = {"engine": "google_lens", "url": catbox_url, "api_key": settings.SERPAPI_API_KEY}
    s_res = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
    s_data = s_res.json()
    out.append(f"SerpApi with Catbox Keys: {list(s_data.keys())}")
    if "visual_matches" in s_data:
        out.append(f"SUCCESS (Catbox)! {len(s_data['visual_matches'])} visual matches found!")
        for m in s_data["visual_matches"][:3]:
            out.append(f"  Match: {m.get('title')} -> {m.get('link')}")
    elif "exact_matches" in s_data:
        out.append(f"SUCCESS (Catbox)! {len(s_data['exact_matches'])} exact matches found!")
except Exception as e:
    out.append(f"Catbox error: {e}")

# Host 2: Freeimage.host (using public demo key)
try:
    f_res = requests.post(
        "https://freeimage.host/api/1/upload",
        data={"key": "6d207e641c42fc5f885b412e300ccf42", "action": "upload", "format": "json"},
        files={"source": ("elon.jpg", compressed_bytes, "image/jpeg")},
        timeout=15
    )
    out.append(f"Freeimage status: {f_res.status_code}")
    if f_res.status_code == 200:
        f_data = f_res.json()
        free_url = f_data.get("image", {}).get("url", "")
        out.append(f"Freeimage URL: {free_url}")

        params = {"engine": "google_lens", "url": free_url, "api_key": settings.SERPAPI_API_KEY}
        s_res2 = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
        s_data2 = s_res2.json()
        out.append(f"SerpApi with Freeimage Keys: {list(s_data2.keys())}")
        if "visual_matches" in s_data2:
            out.append(f"SUCCESS (Freeimage)! {len(s_data2['visual_matches'])} visual matches found!")
            for m in s_data2["visual_matches"][:3]:
                out.append(f"  Match: {m.get('title')} -> {m.get('link')}")
except Exception as e:
    out.append(f"Freeimage error: {e}")

with open(BASE_DIR / "host_test_out.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("DONE HOSTING TEST")
