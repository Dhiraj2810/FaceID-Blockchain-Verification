import time
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.pipeline.orchestrator import PipelineOrchestrator
from app.crypto.hashing import sha256_file
from app.blockchain.verifier import BlockchainService

app = FastAPI(
    title="Face Identification & Blockchain Verification API",
    description="Production-quality prototype for face detection, reverse search, and Web3 evidence registration.",
    version="1.0.0"
)

# Minimal CORS Configuration required for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve results, input, and test fixtures as static routes
app.mount("/results", StaticFiles(directory=settings.RESULTS_DIR), name="results")

if settings.INPUT_DIR.exists():
    app.mount("/input", StaticFiles(directory=settings.INPUT_DIR), name="input")

base_dir = settings.INPUT_DIR.parent
tests_dir = base_dir / "tests"
if tests_dir.exists():
    app.mount("/tests", StaticFiles(directory=tests_dir), name="tests")

orchestrator = PipelineOrchestrator()
blockchain_service = BlockchainService()


@app.get("/")
def health_check():
    return {
        "status": "ONLINE",
        "service": "FaceChain Verifier API",
        "threshold": settings.FACE_MATCH_THRESHOLD,
        "contract_address": settings.CONTRACT_ADDRESS,
        "network": settings.NETWORK_NAME
    }


@app.post("/verify")
async def verify_image(image: UploadFile = File(...)):
    """
    Accepts an uploaded face image, runs full detection, reverse image search,
    face matching, SHA-256 fingerprinting, and blockchain registration.
    """
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a valid image (JPG/PNG).")

    timestamp = int(time.time())
    temp_filename = f"upload_{timestamp}_{image.filename}"
    temp_path = settings.INPUT_DIR / temp_filename

    try:
        contents = await image.read()
        with open(temp_path, "wb") as f:
            f.write(contents)

        pipeline_result = orchestrator.run_pipeline(str(temp_path), verbose=True)

        # Cleanup temporary uploaded file
        if temp_path.exists():
            temp_path.unlink()

        return pipeline_result.model_dump()

    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        raise HTTPException(status_code=500, detail=f"Pipeline processing error: {str(e)}")


@app.post("/tamper-test")
async def tamper_test(payload: dict = Body(...)):
    """
    Demonstrates tamper verification by evaluating the original hash vs a simulated tampered file hash.
    Accepts: {"evidence_path": str, "record_id": int} or finds the latest evidence file in results/.
    """
    evidence_path_str = payload.get("evidence_path")
    record_id = payload.get("record_id")
    mode = payload.get("mode", "tamper")  # 'original' or 'tamper'

    if not evidence_path_str:
        # Find latest file in results directory
        files = sorted(settings.RESULTS_DIR.glob("matched_*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            raise HTTPException(status_code=400, detail="No registered evidence file found in results/ directory.")
        evidence_path = files[0]
    else:
        evidence_path = Path(evidence_path_str)

    if not evidence_path.exists():
        raise HTTPException(status_code=404, detail=f"Evidence file not found: {evidence_path}")

    # Fetch original on-chain hash
    if record_id is not None:
        rec = blockchain_service.get_record(record_id)
        on_chain_hash = rec.get("content_hash", "")
    else:
        on_chain_hash = sha256_file(evidence_path)

    original_hash = sha256_file(evidence_path)

    if mode == "original":
        current_hash = original_hash
        verified = (current_hash == on_chain_hash)
        status = "VERIFIED" if verified else "TAMPERED"
    else:
        # Simulate harmless modification to bytes without overwriting original file
        with open(evidence_path, "rb") as f:
            data = f.read()
        tampered_bytes = data + b"\x00TAMPERED_DEMO_BYTE"
        from app.crypto.hashing import sha256_bytes
        current_hash = sha256_bytes(tampered_bytes)
        verified = (current_hash == on_chain_hash)
        status = "VERIFIED" if verified else "TAMPERED"

    return {
        "mode": mode,
        "evidence_file": evidence_path.name,
        "original_hash": original_hash,
        "current_hash": current_hash,
        "on_chain_hash": on_chain_hash,
        "verified": verified,
        "status": status
    }


@app.delete("/records/{filename}")
async def delete_specific_record(filename: str):
    """
    Completely deletes a specific image record (e.g. matched_1788717264.jpg)
    and its associated raw search log file from the results directory.
    """
    results_dir = settings.RESULTS_DIR
    target_file = results_dir / filename
    
    deleted_files = []
    
    # 1. Delete target image file
    if target_file.exists() and target_file.is_file() and target_file.name != ".gitkeep":
        target_file.unlink()
        deleted_files.append(filename)
    
    # 2. Extract timestamp if matched_<timestamp>.jpg or search_raw_<timestamp>.json
    import re
    timestamp_match = re.search(r"\d{10}", filename)
    if timestamp_match:
        ts = timestamp_match.group(0)
        # Delete corresponding raw search log if present
        for raw_log in results_dir.glob(f"search_raw_*{ts}*.json"):
            if raw_log.exists():
                raw_log.unlink()
                deleted_files.append(raw_log.name)
                
    if not deleted_files:
        raise HTTPException(status_code=404, detail=f"No matching files found for record '{filename}'")
        
    return {
        "status": "success",
        "message": f"Successfully deleted record files for {filename}",
        "deleted_files": deleted_files
    }

