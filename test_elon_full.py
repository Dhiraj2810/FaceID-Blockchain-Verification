import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.pipeline.orchestrator import PipelineOrchestrator

img_path = str(BASE_DIR / "input" / "temp_url_input.jpg")
print("================ TEST ELON MUSK FULL PIPELINE ================")
print("Input file:", img_path)

orchestrator = PipelineOrchestrator()
res = orchestrator.run_pipeline(img_path, verbose=True)

out = []
out.append("================ PIPELINE FINAL RESULTS ================")
out.append(f"Status: {res.status}")
out.append(f"Face Detected: {res.face.get('detected')} (Count: {res.face.get('count')})")
out.append(f"Search Provider: {res.search.get('provider')}")
out.append(f"Candidates Discovered: {res.search.get('candidates_found')}")
if res.match and res.match.get("found"):
    out.append(f"Match Found: YES! Similarity: {res.match.get('similarity', 0.0):.4f}")
    out.append(f"Discovered Source URL: {res.match.get('source_url')}")
    out.append(f"Discovered Title: {res.match.get('candidate_title')}")
    out.append(f"Evidence Saved File: {res.match.get('evidence_image')}")
else:
    out.append("Match Found: NO")

if res.blockchain:
    out.append(f"Blockchain Registered: {res.blockchain.get('registered')}")
    out.append(f"SHA-256 Hash: {res.blockchain.get('hash')}")
    out.append(f"Transaction Hash: {res.blockchain.get('transaction_hash')}")
    out.append(f"Record ID: {res.blockchain.get('record_id')}")
    out.append(f"Network: {res.blockchain.get('network')}")

if res.verification:
    out.append(f"Blockchain Verification Status: {res.verification.get('status')} (Verified: {res.verification.get('verified')})")


with open(BASE_DIR / "elon_full_out.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("FINISHED PIPELINE TEST")
