import time
import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
from urllib.parse import urlparse
from app.config import settings
from app.evidence.models import CandidateResult, CandidateMatch, EvidenceRecord
from app.evidence.downloader import download_candidate_image
from app.face.detector import detect_faces
from app.face.embedding import generate_embedding
from app.face.matcher import compare_embeddings
from app.crypto.hashing import sha256_bytes


import threading

_MODEL_LOCK = threading.Lock()

def eval_single_candidate(args):
    i, candidate, target_embedding, threshold = args
    image_url = candidate.thumbnail_url or candidate.url
    domain = urlparse(candidate.url).netloc or "web"

    img, content_bytes = download_candidate_image(image_url)
    if img is None or content_bytes is None:
        eval_dict = {
            "title": candidate.title,
            "url": candidate.url,
            "thumbnail_url": image_url,
            "domain": domain,
            "similarity": 0.0,
            "matched": False,
            "status": "Download failed"
        }
        log_str = f"\n  Candidate {i}:\n    Source URL : {candidate.url}\n    Status     : Download / Decode failed (Skipped)"
        return i, candidate, None, None, -1.0, eval_dict, log_str

    file_size = len(content_bytes)
    cand_sha256 = sha256_bytes(content_bytes)

    try:
        with _MODEL_LOCK:
            faces, diag = detect_faces(img, fast_mode=True)
    except Exception as e:
        eval_dict = {
            "title": candidate.title,
            "url": candidate.url,
            "thumbnail_url": image_url,
            "domain": domain,
            "similarity": 0.0,
            "matched": False,
            "status": "Detection error"
        }
        log_str = f"\n  Candidate {i}:\n    Source URL : {candidate.url}\n    File Size  : {file_size:,} bytes\n    SHA-256    : {cand_sha256[:16]}...\n    Status     : Face detection error: {e} (Skipped)"
        return i, candidate, None, None, -1.0, eval_dict, log_str

    if not faces:
        reason_msg = "NO MATCH: 0 faces detected in candidate image"
        eval_dict = {
            "title": candidate.title,
            "url": candidate.url,
            "thumbnail_url": image_url,
            "domain": domain,
            "discovery_source": candidate.source,
            "similarity": 0.0,
            "matched": False,
            "status": "0 faces detected",
            "reason": reason_msg
        }
        log_str = (f"\n  Candidate {i}:\n"
                   f"    Source URL   : {candidate.url}\n"
                   f"    Web Discovery: {candidate.source}\n"
                   f"    File Size    : {file_size:,} bytes\n"
                   f"    SHA-256      : {cand_sha256[:16]}...\n"
                   f"    ArcFace Sim  : 0.0000 (NO MATCH)\n"
                   f"    Reason       : {reason_msg}")
        return i, candidate, None, None, -1.0, eval_dict, log_str

    cand_best_sim = -1.0
    cand_best_reason = f"NO MATCH: Similarity score (0.0000) < threshold ({threshold:.4f})"

    for face in faces:
        try:
            with _MODEL_LOCK:
                emb = generate_embedding(face)
            res = compare_embeddings(target_embedding, emb, threshold=threshold)
            sim = res["similarity"]
            reason = res.get("reason", "")
            if sim > cand_best_sim:
                cand_best_sim = sim
                cand_best_reason = reason
        except Exception:
            continue

    is_match = cand_best_sim >= threshold
    status_str = "MATCH" if is_match else "NOT MATCH"
    status_symbol = "✓ MATCH" if is_match else "❌ NO MATCH"

    log_str = (f"\n  Candidate {i}:\n"
               f"    Source URL   : {candidate.url}\n"
               f"    Web Discovery: {candidate.source}\n"
               f"    File Size    : {file_size:,} bytes\n"
               f"    SHA-256      : {cand_sha256[:16]}...\n"
               f"    Faces Seen   : {len(faces)}\n"
               f"    ArcFace Sim  : {cand_best_sim:.4f} ({status_symbol})\n"
               f"    Reason       : {cand_best_reason}")

    eval_dict = {
        "title": candidate.title,
        "url": candidate.url,
        "thumbnail_url": image_url,
        "domain": domain,
        "discovery_source": candidate.source,
        "similarity": max(0.0, float(cand_best_sim)),
        "matched": is_match,
        "status": status_str,
        "reason": cand_best_reason
    }

    return i, candidate, img, content_bytes, cand_best_sim, eval_dict, log_str


def process_candidates(
    candidates: List[CandidateResult],
    target_embedding: np.ndarray,
    threshold: float = None
) -> Tuple[Optional[CandidateMatch], Optional[EvidenceRecord], Optional[str], List[dict]]:
    """
    Downloads candidate images safely and concurrently, detects ALL faces in each candidate image,
    computes ArcFace embeddings for every detected face, compares against the target embedding,
    and identifies the highest-scoring candidate exceeding the matching threshold.
    Returns:
        (best_match, evidence_record, evidence_image_path, candidate_evaluations)
    """
    if threshold is None:
        threshold = settings.FACE_MATCH_THRESHOLD

    best_match = None
    best_similarity = -1.0
    best_candidate = None
    best_image = None
    best_content_bytes = None
    candidate_evaluations = []

    print(f"\n[5/7] Verifying candidates against target face embedding (Threshold >= {threshold:.2f})")

    from concurrent.futures import ThreadPoolExecutor

    task_args = [(i, candidate, target_embedding, threshold) for i, candidate in enumerate(candidates, 1)]
    max_workers = min(8, max(1, len(candidates)))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(eval_single_candidate, task_args))

    results.sort(key=lambda x: x[0])

    for i, candidate, img, content_bytes, sim, eval_dict, log_str in results:
        print(log_str)
        candidate_evaluations.append(eval_dict)
        if sim > best_similarity:
            best_similarity = sim
            best_candidate = candidate
            best_image = img
            best_content_bytes = content_bytes

    if best_candidate and best_similarity >= threshold and best_image is not None:
        timestamp = int(time.time())
        evidence_filename = f"matched_{timestamp}.jpg"
        evidence_path = settings.RESULTS_DIR / evidence_filename

        # Write exact downloaded candidate bytes to preserve cryptographic binary integrity
        if best_content_bytes:
            with open(evidence_path, "wb") as f:
                f.write(best_content_bytes)
        else:
            cv2.imwrite(str(evidence_path), best_image)

        match_result = CandidateMatch(
            matched=True,
            similarity=best_similarity,
            candidate_url=best_candidate.url,
            candidate_title=best_candidate.title,
            candidate_image=str(evidence_path)
        )

        evidence_record = EvidenceRecord(
            source_url=best_candidate.url,
            title=best_candidate.title,
            search_provider=best_candidate.source,
            face_similarity=best_similarity,
            image_path=str(evidence_path)
        )

        candidate_evaluations.sort(key=lambda x: x["similarity"], reverse=True)
        return match_result, evidence_record, str(evidence_path), candidate_evaluations

    candidate_evaluations.sort(key=lambda x: x["similarity"], reverse=True)
    return None, None, None, candidate_evaluations

