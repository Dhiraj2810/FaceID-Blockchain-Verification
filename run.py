import os
import sys
import argparse
from pathlib import Path

# Ensure UTF-8 output encoding for Windows terminal unicode safety
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from app.config import settings
from app.pipeline.orchestrator import PipelineOrchestrator
from app.crypto.hashing import sha256_file
from app.blockchain.verifier import BlockchainService


def check_configuration():
    print("Checking configuration...")
    serp_ok = "✓ SERPAPI_API_KEY" if settings.SERPAPI_API_KEY and not settings.SERPAPI_API_KEY.startswith("your_") else "❌ SERPAPI_API_KEY (Not Configured)"
    rpc_ok = "✓ RPC_URL" if settings.RPC_URL and not settings.RPC_URL.startswith("0x") and "your_" not in settings.RPC_URL else "⚠ RPC_URL (Using Local Web3 Simulator)"

    if settings.CONTRACT_ADDRESS and settings.CONTRACT_ADDRESS != "0x0000000000000000000000000000000000000000":
        contract_ok = "✓ CONTRACT_ADDRESS"
    else:
        contract_ok = "❌ CONTRACT_ADDRESS is not configured in .env"

    thresh_ok = f"✓ FACE_MATCH_THRESHOLD ({settings.FACE_MATCH_THRESHOLD:.2f})"

    print(f"  {serp_ok}")
    print(f"  {rpc_ok}")
    print(f"  {contract_ok}")
    print(f"  {thresh_ok}\n")


def run_self_test():
    print("==================================================")
    print(" SYSTEM SELF TEST")
    print("==================================================")

    all_passed = True

    # 1. Python environment
    print(f"✓ Python Version: {sys.version.split()[0]}")

    # 2. InsightFace import
    try:
        import insightface
        print("✓ InsightFace installed")
    except ImportError:
        print("❌ InsightFace NOT installed")
        all_passed = False

    # 3. ONNX Runtime & Providers
    try:
        import onnxruntime as ort
        providers = ort.get_available_providers()
        print(f"✓ ONNX Runtime available (Providers: {', '.join(providers)})")
    except ImportError:
        print("❌ ONNX Runtime NOT installed")
        all_passed = False

    # 4. Face Detector Initialization
    try:
        from app.face.detector import get_face_analyzer
        analyzer = get_face_analyzer()
        if analyzer is not None:
            print("✓ Face detector & ArcFace embedding model (buffalo_l) loaded")
        else:
            print("❌ Face detector initialization failed")
            all_passed = False
    except Exception as e:
        print(f"❌ Face detector initialization error: {e}")
        all_passed = False

    # 5. SerpApi Configuration
    if settings.SERPAPI_API_KEY and not settings.SERPAPI_API_KEY.startswith("your_"):
        print("✓ SerpApi key configured")
    else:
        print("❌ SerpApi key NOT configured in .env")
        all_passed = False

    # 6. Blockchain RPC
    if settings.RPC_URL and "your_" not in settings.RPC_URL:
        print(f"✓ Blockchain RPC configured ({settings.RPC_URL[:30]}...)")
    else:
        print("⚠ Blockchain RPC not set (Will fallback to simulated Web3 node)")

    # 7. Contract Address
    if settings.CONTRACT_ADDRESS and settings.CONTRACT_ADDRESS != "0x0000000000000000000000000000000000000000":
        print(f"✓ Contract address configured ({settings.CONTRACT_ADDRESS})")
    else:
        print("❌ Contract address NOT configured in .env")
        all_passed = False

    print("==================================================")
    if all_passed:
        print("SYSTEM READY")
    else:
        print("SYSTEM NOT READY - Please resolve reported errors above.")
    print("==================================================")


def run_cli():
    parser = argparse.ArgumentParser(
        description="Face Identification & Blockchain Verification Pipeline CLI"
    )
    parser.add_argument(
        "--image",
        type=str,
        default="input/test.jpg",
        help="Path to input face image"
    )
    parser.add_argument(
        "--demo-tamper",
        action="store_true",
        help="Run live pipeline followed by evidence tamper simulation"
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run system self-test and verify all model & API dependencies"
    )
    args = parser.parse_args()

    if args.self_test:
        run_self_test()
        return

    print("==================================================")
    print(" FACE IDENTIFICATION & BLOCKCHAIN VERIFIER")
    print("==================================================")

    check_configuration()

    orchestrator = PipelineOrchestrator()

    if not getattr(args, "demo_tamper", False):
        orchestrator.run_pipeline(args.image, verbose=True)
        print("==================================================")
        return

    # ----------------------------------------------------
    # TAMPER DEMONSTRATION MODE
    # ----------------------------------------------------
    print("[Step 1/2] Running standard pipeline to generate registered evidence...")
    res = orchestrator.run_pipeline(args.image, verbose=True)

    if res.status != "success" or not res.match or not res.match.get("found"):
        print("\n❌ Cannot execute tamper demo: Pipeline did not register valid evidence.")
        return

    evidence_file = res.match["evidence_image"]
    record_id = res.blockchain["record_id"]
    original_hash = res.blockchain["hash"]

    print("\n==================================================")
    print(" TAMPER DEMONSTRATION MODE")
    print("==================================================")
    print(f"Modifying evidence file: {evidence_file}")

    # Tamper with file by appending byte data
    with open(evidence_file, "ab") as f:
        f.write(b"\x00TAMPERED_CONTENT_DATA")

    modified_hash = sha256_file(evidence_file)

    service = BlockchainService()
    record_data = service.get_record(record_id)
    on_chain_hash = record_data["content_hash"]

    print(f"\nOriginal Hash : {original_hash[:16]}...")
    print(f"Modified Hash : {modified_hash[:16]}...")
    print(f"On-Chain Hash : {on_chain_hash[:16]}...")

    if modified_hash != on_chain_hash:
        print("\n❌ TAMPER DETECTED: Content fingerprint no longer matches Blockchain record!")
    else:
        print("\n✅ VERIFIED")
    print("==================================================")


if __name__ == "__main__":
    run_cli()
