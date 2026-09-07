import json
from typing import Dict, Any, Tuple
from web3 import Web3
from eth_account import Account
from app.config import settings

CONTRACT_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "recordId", "type": "uint256"},
            {"indexed": True, "internalType": "bytes32", "name": "contentHash", "type": "bytes32"},
            {"indexed": False, "internalType": "string", "name": "sourceUrl", "type": "string"},
            {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"}
        ],
        "name": "RecordStored",
        "type": "event"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "recordId", "type": "uint256"}
        ],
        "name": "getRecord",
        "outputs": [
            {"internalType": "bytes32", "name": "contentHash", "type": "bytes32"},
            {"internalType": "string", "name": "sourceUrl", "type": "string"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getRecordCount",
        "outputs": [
            {"internalType": "uint256", "name": "", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "contentHash", "type": "bytes32"},
            {"internalType": "string", "name": "sourceUrl", "type": "string"}
        ],
        "name": "storeRecord",
        "outputs": [
            {"internalType": "uint256", "name": "recordId", "type": "uint256"}
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# Standard contract bytecode compiled for offline mock tester deployment if needed
CONTRACT_BYTECODE = "0x608060405234801561001057600080fd5b506102aa806100206000396000f3fe"


class SimulatedBlockchainNode:
    """
    In-memory fallback Ethereum blockchain simulator when live RPC/PrivateKey are not configured.
    Maintains real state, auto-increments transaction hashes and record IDs.
    """
    def __init__(self):
        self.records = []

    def store_record(self, content_hash_bytes: bytes, source_url: str) -> Tuple[str, int]:
        record_id = len(self.records)
        import time, hashlib
        tx_hash = "0x" + hashlib.sha256(f"{record_id}:{content_hash_bytes.hex()}:{time.time()}".encode()).hexdigest()
        timestamp = int(time.time())

        self.records.append({
            "contentHash": content_hash_bytes,
            "sourceUrl": source_url,
            "timestamp": timestamp
        })
        return tx_hash, record_id

    def get_record(self, record_id: int) -> Tuple[bytes, str, int]:
        if record_id < 0 or record_id >= len(self.records):
            raise ValueError(f"Record ID {record_id} out of bounds.")
        rec = self.records[record_id]
        return rec["contentHash"], rec["sourceUrl"], rec["timestamp"]


_SIMULATED_NODE = SimulatedBlockchainNode()


def is_live_configured() -> bool:
    """
    Returns True if valid Web3 RPC URL and Private Key are configured.
    """
    url = settings.RPC_URL.strip()
    key = settings.PRIVATE_KEY.strip()
    return bool(url and key and url.startswith("http") and not key.startswith("0xyour"))
