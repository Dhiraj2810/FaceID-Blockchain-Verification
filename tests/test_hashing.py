import pytest
import tempfile
from pathlib import Path
from app.crypto.hashing import sha256_file, hex_to_bytes32, bytes32_to_hex


def test_sha256_file_consistency():
    with tempfile.NamedTemporaryFile("wb", delete=False) as f:
        f.write(b"Hello World Evidence Content")
        temp_path = f.name

    try:
        hash1 = sha256_file(temp_path)
        hash2 = sha256_file(temp_path)

        assert hash1 == hash2
        assert len(hash1) == 64
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_sha256_file_tampering_detection():
    with tempfile.NamedTemporaryFile("wb", delete=False) as f:
        f.write(b"Original Evidence Content")
        temp_path = f.name

    try:
        original_hash = sha256_file(temp_path)

        # Alter 1 byte
        with open(temp_path, "ab") as f:
            f.write(b"TAMPERED")

        modified_hash = sha256_file(temp_path)

        assert original_hash != modified_hash
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_hex_to_bytes32_conversion():
    sample_hex = "a" * 64
    b32 = hex_to_bytes32(sample_hex)

    assert isinstance(b32, bytes)
    assert len(b32) == 32

    reconstructed_hex = bytes32_to_hex(b32)
    assert reconstructed_hex == "0x" + sample_hex
