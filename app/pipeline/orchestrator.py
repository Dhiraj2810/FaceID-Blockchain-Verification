import os
import sys
import cv2
from pathlib import Path
from typing import Optional, Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.config import settings
from app.face.detector import detect_faces, load_image
from app.face.embedding import generate_embedding
from app.search.serpapi_lens import SerpApiLensSearcher
from app.evidence.extractor import process_candidates
from app.crypto.hashing import sha256_file
from app.blockchain.verifier import BlockchainService
from app.evidence.models import PipelineResult


class PipelineOrchestrator:
    """
    Main orchestrator executing the 7-stage Face Identification & Blockchain Verification pipeline.
    Enforces honest execution: zero fake fallbacks, real ArcFace embeddings, real SerpApi Lens calls,
    and blockchain registration only upon genuine face verification.
    """

    def __init__(self, searcher=None, blockchain_service=None):
        self.searcher = searcher or SerpApiLensSearcher()
        self.blockchain_service = blockchain_service or BlockchainService()

    def run_pipeline(
        self,
        image_path: str,
        verbose: bool = True,
        threshold: Optional[float] = None
    ) -> PipelineResult:
        thresh = threshold if threshold is not None else settings.FACE_MATCH_THRESHOLD
        result = PipelineResult()
        path = Path(image_path)

        # ----------------------------------------------------
        # [1/7] Loading image
        # ----------------------------------------------------
        if verbose:
            print("[1/7] Loading input image")

        try:
            bgr_img, meta = load_image(image_path)
            if verbose:
                print(f"      ✓ Input image loaded ({meta['width']}x{meta['height']}, {meta['channels']} channels)")
        except Exception as e:
            err_msg = f"Failed to load/decode image: {e}"
            if verbose:
                print(f"      ❌ {err_msg}")
            result.status = "error"
            result.message = err_msg
            return result

        # ----------------------------------------------------
        # [2/7] Detecting face
        # ----------------------------------------------------
        if verbose:
            print("\n[2/7] Detecting face")
            print("      Model      : InsightFace buffalo_l")
            print("      Detector   : SCRFD")
            print("      Runtime    : CPU")
            print(f"      Detection  : {settings.FACE_DET_SIZE}x{settings.FACE_DET_SIZE}")
            print(f"      Threshold  : {settings.FACE_DET_THRESHOLD:.2f}")

        try:
            faces, diagnostics = detect_faces(bgr_img)
            if verbose:
                for log_entry in diagnostics.get("attempts_log", []):
                    print(f"      {log_entry}")
        except Exception as e:
            err_msg = f"InsightFace detection engine failure: {e}"
            if verbose:
                print(f"\n      ❌ {err_msg}")
            result.status = "error"
            result.message = err_msg
            return result

        face_count = len(faces)

        if face_count == 0:
            err_msg = "No face detected in input image."
            if verbose:
                print("\n      ❌ No face detected in input image.")
                print("\n      Diagnostics:")
                print(f"        Image size     : {diagnostics['image_size']}")
                print(f"        Detection      : {diagnostics['detection_model']}")
                print(f"        Detection size : {diagnostics['det_size']}")
                print(f"        Threshold      : {diagnostics['threshold']}")
                print(f"        Attempts       : {diagnostics['attempts']}")
                print("\n      Possible causes:")
                print("      - face too small")
                print("      - extreme pose")
                print("      - image too blurry")
                print("      - poor lighting")
                print("      - face partially occluded")

            result.status = "error"
            result.message = err_msg
            result.face = {"detected": False, "count": 0}
            return result

        if face_count > 1:
            err_msg = f"Multiple faces ({face_count}) detected in primary target image. Require exactly 1 primary face."
            if verbose:
                print(f"\n      ❌ Multiple faces ({face_count}) detected.")
                print("      Please provide an image containing one primary face.")

            result.status = "error"
            result.message = err_msg
            result.face = {"detected": True, "count": face_count}
            return result

        # Exactly 1 face detected
        target_face = faces[0]
        if verbose:
            print("      ✓ 1 face detected")

        result.face = {"detected": True, "count": 1}

        # ----------------------------------------------------
        # [3/7] Generating face embedding
        # ----------------------------------------------------
        if verbose:
            print("\n[3/7] Generating face embedding")

        try:
            target_embedding = generate_embedding(target_face)
            if verbose:
                print("      ✓ ArcFace 512-d embedding generated")
        except Exception as e:
            err_msg = f"ArcFace embedding generation failed: {e}"
            if verbose:
                print(f"      ❌ {err_msg}")
            result.status = "error"
            result.message = err_msg
            return result

        # ----------------------------------------------------
        # [4/7] Performing identity-focused reverse image search
        # ----------------------------------------------------
        if verbose:
            print("\n[4/7] Performing identity-focused reverse image search")
            print("      Primary Strategy  : Identity-Focused Face Crop Search")
            print("      Fallback Strategy : Full Scene Image Search")

        candidates = []
        seen_urls = set()
        face_crop_file = None

        try:
            # 1. Create identity-focused face crop search representation
            if "crop" in target_face and target_face["crop"] is not None and target_face["crop"].size > 0:
                bbox = target_face.get("bbox", [0, 0, meta["width"], meta["height"]])
                x1, y1, x2, y2 = bbox
                h_b, w_b = y2 - y1, x2 - x1
                # Add 20% proportional margin to capture full head shape while excluding clothing/background
                pad_x = int(w_b * 0.2)
                pad_y = int(h_b * 0.2)
                cx1 = max(0, x1 - pad_x)
                cy1 = max(0, y1 - pad_y)
                cx2 = min(meta["width"], x2 + pad_x)
                cy2 = min(meta["height"], y2 + pad_y)

                face_crop_img = bgr_img[cy1:cy2, cx1:cx2]
                if face_crop_img.size > 0:
                    import time
                    crop_filename = f"temp_face_crop_{int(time.time())}.jpg"
                    face_crop_file = settings.INPUT_DIR / crop_filename
                    cv2.imwrite(str(face_crop_file), face_crop_img)

            # 2 & 3. Execute Dual-Strategy Search concurrently via ThreadPoolExecutor
            from concurrent.futures import ThreadPoolExecutor
            target_search_path = meta.get("original_url") or meta["path"]

            with ThreadPoolExecutor(max_workers=2) as executor:
                future_face = executor.submit(self.searcher.search, str(face_crop_file)) if (face_crop_file and face_crop_file.exists()) else None
                future_full = executor.submit(self.searcher.search, target_search_path)

                if future_face:
                    try:
                        cands_face = future_face.result()
                        if verbose:
                            print(f"      ✓ Identity-Focused Face Search: {len(cands_face)} candidates discovered")
                        for c in cands_face:
                            if c.url not in seen_urls:
                                seen_urls.add(c.url)
                                c.source = f"{c.source} (Identity-Focused Face Crop)"
                                candidates.append(c)
                    except Exception as ex_f:
                        if verbose:
                            print(f"      ⚠ Identity-Focused Search notice: {ex_f}")

                try:
                    cands_full = future_full.result()
                    if verbose:
                        print(f"      ✓ Full Scene Image Search (Fallback): {len(cands_full)} candidates discovered")
                    for c in cands_full:
                        if c.url not in seen_urls:
                            seen_urls.add(c.url)
                            c.source = f"{c.source} (Full Scene Fallback)"
                            candidates.append(c)
                except Exception as ex_s:
                    if not candidates:
                        raise ex_s
                    elif verbose:
                        print(f"      ⚠ Full Scene Search notice: {ex_s}")

            # Cleanup temporary face crop file
            if face_crop_file and face_crop_file.exists():
                try:
                    face_crop_file.unlink()
                except Exception:
                    pass

            candidate_count = len(candidates)
            if verbose:
                print(f"      ✓ Combined & Deduplicated Web Candidates: {candidate_count} total candidate web posts")

            result.search = {
                "provider": "Google Lens (Dual-Strategy)",
                "candidates_found": candidate_count,
                "candidates": []
            }
        except Exception as e:
            if face_crop_file and face_crop_file.exists():
                try:
                    face_crop_file.unlink()
                except Exception:
                    pass
            err_msg = f"{e}"
            if verbose:
                print(f"      ❌ {err_msg}")
            result.status = "error"
            result.message = err_msg
            return result


        if not candidates:
            err_msg = "Google Lens returned no candidate results."
            if verbose:
                print(f"      ⚠ {err_msg}")
                print("      ❌ No verified web evidence was found. Blockchain registration skipped.")
            result.status = "warning"
            result.message = err_msg
            result.match = {"found": False}
            return result

        # ----------------------------------------------------
        # [5/7] Verifying candidates
        # ----------------------------------------------------
        match_res, evidence_rec, evidence_path, candidate_evals = process_candidates(
            candidates,
            target_embedding,
            threshold=thresh
        )

        result.search["candidates"] = candidate_evals

        if not match_res or not evidence_rec or not evidence_path:
            err_msg = "No candidate face met the similarity threshold."
            if verbose:
                print("\n      ❌ No sufficiently similar face found in discovered candidate images.")
                print("      ❌ No verified web evidence was found. Blockchain registration skipped.")
            result.status = "warning"
            result.message = err_msg
            result.match = {"found": False}
            return result

        filename = Path(evidence_path).name
        result.match = {
            "found": True,
            "similarity": match_res.similarity,
            "source_url": match_res.candidate_url,
            "candidate_title": match_res.candidate_title,
            "evidence_image": f"/results/{filename}",
            "evidence_path": evidence_path
        }

        # ----------------------------------------------------
        # [6/7] Registering evidence
        # ----------------------------------------------------
        if verbose:
            print("\n[6/7] Registering evidence on Blockchain")

        local_sha256 = sha256_file(evidence_path)
        evidence_filename = Path(evidence_path).name

        if verbose:
            print("      Selected Evidence Chain:")
            print(f"        • Candidate URL      : {match_res.candidate_url}")
            print(f"        • Similarity Score   : {match_res.similarity:.2f}")
            print(f"        • Evidence Filename  : {evidence_filename}")
            print(f"        • Evidence SHA-256   : {local_sha256}")

        try:
            chain_record = self.blockchain_service.store_evidence(
                content_hash_hex=local_sha256,
                source_url=match_res.candidate_url
            )
            if verbose:
                print(f"        • Blockchain Record  : {chain_record.transaction_hash}")
                print("      ✓ Blockchain transaction submitted")

            result.blockchain = {
                "registered": True,
                "hash": local_sha256,
                "transaction_hash": chain_record.transaction_hash,
                "record_id": chain_record.record_id,
                "contract_address": chain_record.contract_address,
                "network": chain_record.network
            }
        except Exception as e:
            err_msg = f"Blockchain registration failed: {e}. Evidence was found, but blockchain recording did not complete."
            if verbose:
                print(f"      ❌ {err_msg}")
            result.status = "error"
            result.message = err_msg
            return result

        # ----------------------------------------------------
        # [7/7] Re-verifying
        # ----------------------------------------------------
        if verbose:
            print("\n[7/7] Re-verifying evidence against Blockchain record")

        verification_res = self.blockchain_service.verify_evidence(
            file_path=evidence_path,
            record_id=chain_record.record_id
        )

        if verbose:
            print(f"      Local Hash : {verification_res.local_hash[:16]}...")
            print(f"      Chain Hash : {verification_res.on_chain_hash[:16]}...")
            if verification_res.verified:
                print("\n      ✅ BLOCKCHAIN VERIFIED")
            else:
                print("\n      ❌ TAMPER DETECTED")

            print(f"\nTransaction Hash:")
            print(f"{chain_record.transaction_hash}\n")

        result.verification = {
            "verified": verification_res.verified,
            "local_hash": verification_res.local_hash,
            "on_chain_hash": verification_res.on_chain_hash,
            "status": verification_res.status
        }

        return result
