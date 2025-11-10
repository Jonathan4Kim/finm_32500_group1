"""Tests for metadata serialization helpers."""

import uuid

import pytest

from shared_memory_utils import SharedMemoryMetadata


def _unique_name(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def test_metadata_roundtrip_preserves_payload():
    name = _unique_name("meta_roundtrip")
    metadata = SharedMemoryMetadata(name=name, create=True)
    try:
        payload = {"symbols": ["AAPL", "MSFT"], "price_book_name": "price_book"}
        metadata.write(payload)
        assert metadata.read() == payload
    finally:
        metadata.close()
        metadata.unlink()


def test_metadata_write_rejects_payloads_exceeding_buffer():
    name = _unique_name("meta_overflow")
    metadata = SharedMemoryMetadata(name=name, create=True)
    try:
        oversized = "x" * SharedMemoryMetadata.METADATA_SIZE
        with pytest.raises(ValueError):
            metadata.write({"blob": oversized})
    finally:
        metadata.close()
        metadata.unlink()

