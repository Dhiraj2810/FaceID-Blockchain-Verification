import hashlib
from pathlib import Path


def sha256_file(file_path: str | Path) -> str:
    """
    Computes the SHA-256 cryptographic hex digest of a file.
    Reads file in binary chunks to handle large evidence files safely.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Evidence file not found: {file_path}")

    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)

    return hasher.hexdigest()


def sha256_bytes(data: bytes) -> str:
    """
    Computes the SHA-256 cryptographic hex digest of raw bytes.
    """
    return hashlib.sha256(data).hexdigest()


def hex_to_bytes32(hex_str: str) -> bytes:
    """
    Converts a 64-character SHA-256 hex string into a 32-byte representation suitable
    for Solidity bytes32 types.
    """
    clean_hex = hex_str.lower().strip()
    if clean_hex.startswith("0x"):
        clean_hex = clean_hex[2:]

    if len(clean_hex) != 64:
        raise ValueError(
            f"Invalid SHA-256 hex length ({len(clean_hex)}). Expected 64 characters."
        )

    return bytes.fromhex(clean_hex)


def bytes32_to_hex(b32: bytes) -> str:
    """
    Converts a 32-byte Solidity bytes32 representation to a 0x-prefixed hex string.
    """
    if isinstance(b32, str):
        if b32.startswith("0x"):
            return b32.lower()
        return "0x" + b32.lower()
    return "0x" + b32.hex()
