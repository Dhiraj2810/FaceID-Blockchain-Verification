import os
import cv2
import numpy as np
from pathlib import Path
from typing import Union, List, Dict, Any, Tuple
from app.config import settings

_FACE_ANALYZER = None


def get_face_analyzer():
    """
    Initializes the InsightFace FaceAnalysis instance ONCE.
    Avoids unnecessary reinitializations across detection attempts.
    """
    global _FACE_ANALYZER
    if _FACE_ANALYZER is not None:
        return _FACE_ANALYZER

    try:
        import insightface
        from insightface.app import FaceAnalysis
        import onnxruntime as ort

        available_providers = ort.get_available_providers()
        providers = ["CPUExecutionProvider"]
        if "CUDAExecutionProvider" in available_providers:
            providers.insert(0, "CUDAExecutionProvider")

        det_size = settings.FACE_DET_SIZE
        det_thresh = settings.FACE_DET_THRESHOLD

        analyzer = FaceAnalysis(
            name="buffalo_l",
            allowed_modules=["detection", "recognition"],
            providers=providers
        )
        analyzer.prepare(
            ctx_id=-1,
            det_size=(det_size, det_size),
            det_thresh=det_thresh
        )
        _FACE_ANALYZER = analyzer
        return _FACE_ANALYZER

    except Exception as e:
        raise RuntimeError(f"InsightFace initialization failed: {e}. Please ensure dependencies are properly installed.")


def load_image(image_input: Union[str, Path, np.ndarray]) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Loads an image from file path or validates a numpy array.
    Ensures correct BGR uint8 contiguous format for InsightFace.
    """
    original_url = None
    if isinstance(image_input, (str, Path)):
        path_str = str(image_input).replace("\\", "/")
        if path_str.startswith("http://") or path_str.startswith("https://"):
            original_url = path_str
            import requests
            url_target = settings.INPUT_DIR / "temp_url_input.jpg"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            resp = requests.get(path_str, headers=headers, timeout=settings.REQUEST_TIMEOUT)
            if resp.status_code == 200:
                with open(url_target, "wb") as f:
                    f.write(resp.content)
                path_str = str(url_target)
            else:
                raise ValueError(f"Unable to download image from URL (HTTP {resp.status_code}): {path_str}")

        if not os.path.exists(path_str):
            raise FileNotFoundError(f"Image file does not exist: {path_str}")

        raw_img = cv2.imread(path_str, cv2.IMREAD_UNCHANGED)
        if raw_img is None or raw_img.size == 0:
            raise ValueError(f"Unable to decode image file: {path_str}")

    elif isinstance(image_input, np.ndarray):
        if image_input.size == 0 or len(image_input.shape) < 2:
            raise ValueError("Provided image array is empty or invalid.")
        raw_img = image_input
        path_str = "<memory_ndarray>"
    else:
        raise ValueError(f"Unsupported image input type: {type(image_input)}")

    # Handle channel formats and ensure standard 3-channel BGR
    if len(raw_img.shape) == 2:
        h, w = raw_img.shape
        c = 1
        bgr_img = cv2.cvtColor(raw_img, cv2.COLOR_GRAY2BGR)
    elif len(raw_img.shape) == 3:
        h, w, c = raw_img.shape
        if c == 4:
            bgr_img = cv2.cvtColor(raw_img, cv2.COLOR_BGRA2BGR)
        elif c == 3:
            bgr_img = raw_img
        else:
            raise ValueError(f"Unsupported channel count: {c}")
    else:
        raise ValueError(f"Invalid image array shape: {raw_img.shape}")

    # Ensure C-contiguous uint8 array
    bgr_img = np.ascontiguousarray(bgr_img, dtype=np.uint8)

    metadata = {
        "path": path_str,
        "original_url": original_url,
        "width": w,
        "height": h,
        "channels": c
    }

    return bgr_img, metadata


def detect_faces(
    image_input: Union[str, Path, np.ndarray],
    fast_mode: bool = False
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Detects faces in the provided image using InsightFace SCRFD model with robust multi-scale strategy:
      - Automatic downscaling for ultra-high-res images (>1920px max side, like 7360x4912 36MP images)
      - Standard 640x640 SCRFD detection size
      - Proportional multi-scale attempts (downscale, upscale for low-res, CLAHE)
      - OpenCV Haar Cascade fallback if InsightFace SCRFD returns 0 faces
    Returns:
        (detected_faces_list, diagnostics_dict)
    """
    bgr_img, meta = load_image(image_input)
    h, w = meta["height"], meta["width"]
    analyzer = get_face_analyzer()

    attempts_log = []
    raw_faces = []
    scale_factor_used = 1.0

    # Ensure det_size is set to optimal 640x640 by default if config is 1024/default
    det_size_val = settings.FACE_DET_SIZE if settings.FACE_DET_SIZE > 0 else 640
    det_thresh_val = settings.FACE_DET_THRESHOLD if settings.FACE_DET_THRESHOLD > 0 else 0.25

    try:
        analyzer.prepare(ctx_id=-1, det_size=(det_size_val, det_size_val), det_thresh=det_thresh_val)
    except Exception:
        pass

    # Strategy 1: If image is ultra-high resolution (>1920px max dim), downscale to max 1280px first
    max_dim = max(w, h)
    if max_dim > 1920:
        scale_1 = 1280.0 / max_dim
        w1, h1 = int(w * scale_1), int(h * scale_1)
        img_scaled1 = cv2.resize(bgr_img, (w1, h1), interpolation=cv2.INTER_AREA)
        faces_attempt1 = analyzer.get(img_scaled1) or []
        attempts_log.append(f"Attempt 1 (downscaled {w1}x{h1} from {w}x{h}): {len(faces_attempt1)} faces detected")

        if faces_attempt1:
            raw_faces = faces_attempt1
            scale_factor_used = scale_1

    # Strategy 2: Try original image if no faces found yet
    if not raw_faces:
        faces_attempt2 = analyzer.get(bgr_img) or []
        attempts_log.append(f"Attempt 2 (original shape {w}x{h}): {len(faces_attempt2)} faces detected")
        if faces_attempt2:
            raw_faces = faces_attempt2
            scale_factor_used = 1.0

    # Strategy 2b: Try Square Letterbox Padded Canvas (prevents aspect ratio distortion in SCRFD)
    if not raw_faces:
        max_s = max(w, h)
        padded_img = np.zeros((max_s, max_s, 3), dtype=np.uint8)
        y_off = (max_s - h) // 2
        x_off = (max_s - w) // 2
        padded_img[y_off:y_off+h, x_off:x_off+w] = bgr_img

        faces_padded = analyzer.get(padded_img) or []
        attempts_log.append(f"Attempt 2b (square padded {max_s}x{max_s}): {len(faces_padded)} faces detected")

        if faces_padded:
            for face in faces_padded:
                if hasattr(face, "bbox"):
                    face.bbox[0] -= x_off
                    face.bbox[2] -= x_off
                    face.bbox[1] -= y_off
                    face.bbox[3] -= y_off
                if hasattr(face, "kps") and face.kps is not None:
                    face.kps[:, 0] -= x_off
                    face.kps[:, 1] -= y_off
            raw_faces = faces_padded
            scale_factor_used = 1.0

    # Strategy 3: Downscale to max side 800px if still no faces found (skipped in fast_mode)
    if not raw_faces and not fast_mode:
        scale_3 = 800.0 / max_dim
        w3, h3 = int(w * scale_3), int(h * scale_3)
        img_scaled3 = cv2.resize(bgr_img, (w3, h3), interpolation=cv2.INTER_AREA)
        faces_attempt3 = analyzer.get(img_scaled3) or []
        attempts_log.append(f"Attempt 3 (downscaled {w3}x{h3}): {len(faces_attempt3)} faces detected")

        if faces_attempt3:
            raw_faces = faces_attempt3
            scale_factor_used = scale_3

    # Strategy 4: Try 1.5x and 2.0x controlled upscaling for small or cropped faces
    if not raw_faces and not fast_mode:
        for scale_4 in [1.5, 2.0]:
            w4, h4 = int(w * scale_4), int(h * scale_4)
            img_scaled4 = cv2.resize(bgr_img, (w4, h4), interpolation=cv2.INTER_CUBIC)
            faces_attempt4 = analyzer.get(img_scaled4) or []
            attempts_log.append(f"Attempt 4 (upscaled {scale_4}x {w4}x{h4}): {len(faces_attempt4)} faces detected")

            if faces_attempt4:
                raw_faces = faces_attempt4
                scale_factor_used = scale_4
                break

    # Strategy 5: Adaptive lower detection threshold (0.15) if still no faces found
    if not raw_faces and not fast_mode:
        try:
            analyzer.prepare(ctx_id=-1, det_size=(det_size_val, det_size_val), det_thresh=0.15)
            faces_attempt5 = analyzer.get(bgr_img) or []
            attempts_log.append(f"Attempt 5 (adaptive det_thresh=0.15): {len(faces_attempt5)} faces detected")
            if faces_attempt5:
                raw_faces = faces_attempt5
                scale_factor_used = 1.0
        except Exception:
            pass

    # Strategy 6: Contrast enhancement (CLAHE) + max 800px resize
    if not raw_faces and not fast_mode:
        scale_6 = min(1.0, 800.0 / max_dim)
        w6, h6 = int(w * scale_6), int(h * scale_6)
        ycrcb = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2YCrCb)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        ycrcb[:, :, 0] = clahe.apply(ycrcb[:, :, 0])
        enhanced_bgr = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)

        if scale_6 != 1.0:
            enhanced_bgr = cv2.resize(enhanced_bgr, (w6, h6), interpolation=cv2.INTER_AREA)

        faces_attempt6 = analyzer.get(enhanced_bgr) or []
        attempts_log.append(f"Attempt 6 (CLAHE enhanced {w6}x{h6}): {len(faces_attempt6)} faces detected")

        if faces_attempt6:
            raw_faces = faces_attempt6
            scale_factor_used = scale_6


    # Process detected InsightFace raw faces
    faces_found = []
    if raw_faces:
        rec_model = analyzer.models.get("recognition") if hasattr(analyzer, "models") else None
        for face in raw_faces:
            if hasattr(face, "bbox"):
                bbox_scaled = face.bbox / scale_factor_used
                x1, y1, x2, y2 = [int(c) for c in bbox_scaled]
            else:
                continue

            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)

            crop = bgr_img[y1:y2, x1:x2]
            confidence = float(face.det_score) if hasattr(face, "det_score") else 1.0

            # If multi-scale detection used a scale factor, scale landmarks and bbox back to original image space
            if scale_factor_used != 1.0:
                face.bbox = bbox_scaled
                if hasattr(face, "kps") and face.kps is not None:
                    face.kps = face.kps / scale_factor_used
                if rec_model is not None and hasattr(face, "kps") and face.kps is not None:
                    try:
                        rec_model.get(bgr_img, face)
                    except Exception:
                        pass

            faces_found.append({
                "bbox": [x1, y1, x2, y2],
                "confidence": round(confidence, 4),
                "crop": crop,
                "raw_face": face
            })


    # Strategy 7: OpenCV Haar Cascade Fallback if InsightFace SCRFD produced 0 faces
    if not faces_found and not fast_mode:
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            face_cascade = cv2.CascadeClassifier(cascade_path)
            gray = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)
            cv_faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(60, 60))
            attempts_log.append(f"Attempt 7 (OpenCV Haar Cascade fallback): {len(cv_faces)} faces detected")

            rec_model = analyzer.models.get("recognition") if hasattr(analyzer, "models") else None

            for (cx, cy, cw, ch) in cv_faces:
                x1, y1, x2, y2 = cx, cy, cx + cw, cy + ch
                crop = bgr_img[y1:y2, x1:x2]

                # Pass crop on a padded 640x640 canvas to InsightFace to extract ArcFace embedding
                h_c, w_c = crop.shape[:2]
                max_c = max(h_c, w_c)
                scale_c = 400.0 / max_c
                cw_s, ch_s = int(w_c * scale_c), int(h_c * scale_c)
                crop_s = cv2.resize(crop, (cw_s, ch_s), interpolation=cv2.INTER_AREA)
                canvas_c = np.zeros((640, 640, 3), dtype=np.uint8)
                canvas_c[(640 - ch_s) // 2 : (640 - ch_s) // 2 + ch_s, (640 - cw_s) // 2 : (640 - cw_s) // 2 + cw_s] = crop_s

                raw_crop_faces = analyzer.get(canvas_c)
                raw_f = None
                if raw_crop_faces:
                    raw_f = raw_crop_faces[0]
                elif rec_model is not None:
                    # Fallback ArcFace embedding generation directly on 112x112 aligned crop
                    try:
                        crop_112 = cv2.resize(crop, (112, 112), interpolation=cv2.INTER_AREA)
                        feat = rec_model.get_feat(crop_112).flatten()
                        from insightface.app.common import Face
                        raw_f = Face(bbox=np.array([x1, y1, x2, y2]), det_score=0.85)
                        raw_f.embedding = feat
                    except Exception:
                        pass


                if raw_f is not None:
                    faces_found.append({
                        "bbox": [x1, y1, x2, y2],
                        "confidence": 0.85,
                        "crop": crop,
                        "raw_face": raw_f
                    })
        except Exception as ex:
            attempts_log.append(f"Attempt 7 Fallback failed: {str(ex)}")


    diagnostics = {
        "image_size": f"{w}x{h}",
        "channels": meta["channels"],
        "detection_model": "SCRFD + MultiScale Strategy",
        "det_size": f"{det_size_val}x{det_size_val}",
        "threshold": det_thresh_val,
        "attempts": len(attempts_log),
        "attempts_log": attempts_log,
        "faces_detected": len(faces_found)
    }

    return faces_found, diagnostics
