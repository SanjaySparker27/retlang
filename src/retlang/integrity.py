"""HMAC-SHA256 integrity helpers, constant-time compare."""

from __future__ import annotations

import hmac
import hashlib


TAG_LEN: int = 32


class IntegrityError(Exception):
    """Raised when HMAC verification fails."""


def compute_tag(key: bytes, data: bytes) -> bytes:
    """Return HMAC-SHA256(key, data)."""
    if not isinstance(key, (bytes, bytearray)):
        raise TypeError("key must be bytes")
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("data must be bytes")
    return hmac.new(bytes(key), bytes(data), hashlib.sha256).digest()


def verify_tag(key: bytes, data: bytes, tag: bytes) -> None:
    """Constant-time verify the tag, raising IntegrityError on mismatch."""
    if len(tag) != TAG_LEN:
        raise IntegrityError("tag length mismatch")
    expected = compute_tag(key, data)
    if not hmac.compare_digest(expected, bytes(tag)):
        raise IntegrityError("HMAC verification failed: ciphertext was tampered or key is wrong")
