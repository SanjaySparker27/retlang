"""Keyed Vigenere-style byte shift.

Given plaintext bytes p and key bytes k:
    c[i] = (p[i] + k[i mod len(k)]) mod 256

This is reversible with:
    p[i] = (c[i] - k[i mod len(k)]) mod 256

This is not a substitute for a real stream cipher; its purpose is to add
a keyed obfuscation layer before the outer alphabet encoding. Integrity
(tamper detection) is handled by an HMAC-SHA256 tag in the envelope.
"""

from __future__ import annotations


def _validate(data: bytes, key: bytes) -> None:
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("data must be bytes")
    if not isinstance(key, (bytes, bytearray)):
        raise TypeError("key must be bytes")
    if len(key) == 0:
        raise ValueError("key must not be empty")


def vigenere_encrypt(data: bytes, key: bytes) -> bytes:
    """Return the encrypted byte string."""
    _validate(data, key)
    key_len = len(key)
    out = bytearray(len(data))
    for i, b in enumerate(data):
        out[i] = (b + key[i % key_len]) & 0xFF
    return bytes(out)


def vigenere_decrypt(data: bytes, key: bytes) -> bytes:
    """Inverse of vigenere_encrypt."""
    _validate(data, key)
    key_len = len(key)
    out = bytearray(len(data))
    for i, b in enumerate(data):
        out[i] = (b - key[i % key_len]) & 0xFF
    return bytes(out)
