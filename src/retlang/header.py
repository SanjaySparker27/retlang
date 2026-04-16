"""Envelope header encoding/decoding.

Envelope layout (big-endian where multi-byte):
    MAGIC       4 bytes  b"SLNG"
    VERSION     1 byte   currently 2
    ITERATIONS  4 bytes  PBKDF2 iterations
    SALT       16 bytes  random salt
    ALPHABET_ID 1 byte   alphabet profile id
    CIPHERTEXT  N bytes  Vigenere output
    HMAC_TAG   32 bytes  HMAC-SHA256 over everything above

VERSION bump history:
    1 -> 2  alphabet profile ids were renumbered when the profile set
            grew from 5 to 11 (see src/retlang/alphabets.py). This is
            pre-release software so we do not maintain a v1 decoder.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

MAGIC: bytes = b"SLNG"
# Bumped from 1 to 2 when the alphabet registry was expanded and renumbered.
VERSION: int = 2
# Parsers accept any version listed here; we currently only read v2.
SUPPORTED_VERSIONS: Tuple[int, ...] = (2,)
HEADER_FIXED_LEN: int = 4 + 1 + 4 + 16 + 1  # 26 bytes
SALT_LEN: int = 16
TAG_LEN: int = 32


@dataclass(frozen=True)
class Header:
    version: int
    iterations: int
    salt: bytes
    alphabet_id: int

    def pack(self) -> bytes:
        if self.version not in SUPPORTED_VERSIONS:
            raise ValueError(f"unsupported version {self.version}")
        if not (0 <= self.iterations <= 0xFFFFFFFF):
            raise ValueError("iterations out of range for 4-byte field")
        if len(self.salt) != SALT_LEN:
            raise ValueError(f"salt must be {SALT_LEN} bytes")
        if not (0 <= self.alphabet_id <= 0xFF):
            raise ValueError("alphabet_id out of byte range")
        return (
            MAGIC
            + bytes([self.version])
            + self.iterations.to_bytes(4, "big")
            + bytes(self.salt)
            + bytes([self.alphabet_id])
        )


def parse_envelope(raw: bytes) -> Tuple[Header, bytes, bytes]:
    """Split raw envelope bytes into (header, ciphertext, tag).

    Raises ValueError on malformed input. Does NOT verify the HMAC.
    """
    if not isinstance(raw, (bytes, bytearray)):
        raise TypeError("raw must be bytes")
    raw = bytes(raw)
    if len(raw) < HEADER_FIXED_LEN + TAG_LEN:
        raise ValueError("envelope too short")

    if raw[:4] != MAGIC:
        raise ValueError("bad magic bytes")
    version = raw[4]
    if version not in SUPPORTED_VERSIONS:
        raise ValueError(f"unsupported version {version}")
    iterations = int.from_bytes(raw[5:9], "big")
    salt = raw[9:25]
    alphabet_id = raw[25]

    body_end = len(raw) - TAG_LEN
    ciphertext = raw[HEADER_FIXED_LEN:body_end]
    tag = raw[body_end:]

    header = Header(
        version=version,
        iterations=iterations,
        salt=salt,
        alphabet_id=alphabet_id,
    )
    return header, ciphertext, tag


def envelope_body(header: Header, ciphertext: bytes) -> bytes:
    """The bytes that HMAC covers: header || ciphertext."""
    return header.pack() + bytes(ciphertext)
