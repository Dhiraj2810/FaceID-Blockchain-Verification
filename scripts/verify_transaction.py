"""
Script to inspect and re-verify a specific transaction or record ID on the blockchain.
"""
import sys
import argparse
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.blockchain.verifier import BlockchainService


def verify_record(record_id: int, file_path: str = None):
    print("==================================================")
    print(" BLOCKCHAIN RECORD INSPECTION & RE-VERIFICATION")
    print("==================================================")

    service = BlockchainService()
    try:
        record = service.get_record(record_id)
        print(f"Record ID    : {record['record_id']}")
        print(f"Content Hash : {record['content_hash']}")
        print(f"Source URL   : {record['source_url']}")
        print(f"Timestamp    : {record['timestamp']}")

        if file_path:
            print("\nComparing against local evidence file:")
            v_res = service.verify_evidence(file_path, record_id)
            print(f"Local Hash   : {v_res.local_hash}")
            print(f"On-Chain Hash: {v_res.on_chain_hash}")
            if v_res.verified:
                print("\n✅ VERIFIED: Local evidence matches on-chain fingerprint!")
            else:
                print("\n❌ TAMPER DETECTED: Evidence file has been altered since registration.")
    except Exception as e:
        print(f"❌ Failed to query record: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect and re-verify blockchain evidence record.")
    parser.add_argument("--record-id", type=int, default=0, help="Record ID on smart contract")
    parser.add_argument("--file", type=str, default=None, help="Optional local evidence file to verify")
    args = parser.parse_args()

    verify_record(args.record_id, args.file)
