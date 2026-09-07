import time
from typing import Dict, Any, Tuple
from web3 import Web3
from eth_account import Account
from app.config import settings
from app.crypto.hashing import sha256_file, hex_to_bytes32, bytes32_to_hex
from app.evidence.models import BlockchainRecord, VerificationResult
from app.blockchain.contract import (
    CONTRACT_ABI,
    _SIMULATED_NODE,
    is_live_configured,
)


class BlockchainService:
    """
    Service for interacting with Ethereum / Sepolia smart contract registry.
    Handles cryptographic hash storage, record querying, and integrity re-verification.
    """

    def __init__(self):
        self.use_live = is_live_configured()
        if self.use_live:
            try:
                self.w3 = Web3(Web3.HTTPProvider(settings.RPC_URL))
                self.account = Account.from_key(settings.PRIVATE_KEY)
                self.contract_address = Web3.to_checksum_address(settings.CONTRACT_ADDRESS)
                self.contract = self.w3.eth.contract(
                    address=self.contract_address,
                    abi=CONTRACT_ABI
                )
            except Exception as e:
                print(f"[BlockchainService] Failed initializing live Web3 provider: {e}. Falling back to simulated node.")
                self.use_live = False

    def store_evidence(self, content_hash_hex: str, source_url: str) -> BlockchainRecord:
        """
        Stores SHA-256 bytes32 fingerprint and metadata on-chain.
        Returns BlockchainRecord object.
        """
        hash_bytes32 = hex_to_bytes32(content_hash_hex)

        if self.use_live:
            try:
                nonce = self.w3.eth.get_transaction_count(self.account.address)
                tx = self.contract.functions.storeRecord(
                    hash_bytes32,
                    source_url
                ).build_transaction({
                    "chainId": settings.CHAIN_ID,
                    "gas": 200000,
                    "gasPrice": self.w3.eth.gas_price,
                    "nonce": nonce,
                })

                signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=settings.PRIVATE_KEY)
                tx_hash_bytes = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash_bytes)

                tx_hash_str = receipt.transactionHash.hex()
                if not tx_hash_str.startswith("0x"):
                    tx_hash_str = "0x" + tx_hash_str

                # Parse event logs to get recordId
                logs = self.contract.events.RecordStored().process_receipt(receipt)
                record_id = logs[0]["args"]["recordId"] if logs else 0

                return BlockchainRecord(
                    transaction_hash=tx_hash_str,
                    record_id=record_id,
                    contract_address=settings.CONTRACT_ADDRESS,
                    network="Sepolia",
                    on_chain_hash=content_hash_hex.lower()
                )
            except Exception as e:
                print(f"[BlockchainService] Live transaction failed: {e}. Falling back to simulated blockchain transaction.")

        # Fallback simulated node transaction
        tx_hash, record_id = _SIMULATED_NODE.store_record(hash_bytes32, source_url)
        return BlockchainRecord(
            transaction_hash=tx_hash,
            record_id=record_id,
            contract_address=settings.CONTRACT_ADDRESS or "0xFaceVerificationRegistrySimulated",
            network="Sepolia (Simulated)",
            on_chain_hash=content_hash_hex.lower()
        )

    def get_record(self, record_id: int) -> Dict[str, Any]:
        """
        Reads evidence record from the smart contract by record ID.
        """
        if self.use_live:
            try:
                content_hash, source_url, timestamp = self.contract.functions.getRecord(record_id).call()
                hash_hex = bytes32_to_hex(content_hash).lower().replace("0x", "")
                return {
                    "record_id": record_id,
                    "content_hash": hash_hex,
                    "source_url": source_url,
                    "timestamp": timestamp
                }
            except Exception as e:
                print(f"[BlockchainService] Live getRecord failed: {e}. Querying simulated node.")

        content_hash_bytes, source_url, timestamp = _SIMULATED_NODE.get_record(record_id)
        hash_hex = content_hash_bytes.hex().lower()
        return {
            "record_id": record_id,
            "content_hash": hash_hex,
            "source_url": source_url,
            "timestamp": timestamp
        }

    def verify_evidence(self, file_path: str, record_id: int) -> VerificationResult:
        """
        Re-verifies evidence file integrity:
        1. Recalculates local file SHA-256 hash.
        2. Retrieves on-chain hash record from smart contract.
        3. Compares local hash vs on-chain hash.
        """
        local_hash = sha256_file(file_path).lower()
        record_data = self.get_record(record_id)
        on_chain_hash = record_data["content_hash"].lower()

        is_verified = (local_hash == on_chain_hash)
        status = "VERIFIED" if is_verified else "TAMPERED"

        return VerificationResult(
            verified=is_verified,
            local_hash=local_hash,
            on_chain_hash=on_chain_hash,
            status=status
        )
