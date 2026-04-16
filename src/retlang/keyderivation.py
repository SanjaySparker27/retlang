"""Key derivation helpers.

We derive a 64-byte block from the passphrase + salt via PBKDF2-HMAC-SHA256
and split it into a 32-byte Vigenere key and a 32-byte HMAC-SHA256 key.

Strength levels
---------------
Named strength levels map to PBKDF2 iteration counts:

    fast     ->   100_000
    normal   ->   200_000 (default)
    strong   ->   500_000
    paranoid -> 1_000_000

`encrypt()` accepts either `strength="normal"` or `iterations=N` but not
both. `decrypt()` always reads the iteration count out of the envelope
header, so ciphertexts encrypted at any strength decrypt transparently.
"""

from __future__ import annotations

import hashlib
import secrets
from typing import Tuple

DEFAULT_ITERATIONS: int = 200_000
SALT_LEN: int = 16
DK_LEN: int = 64
CIPHER_KEY_LEN: int = 32
HMAC_KEY_LEN: int = 32


# Named strength levels.
STRENGTH_ITERATIONS: dict = {
    "fast":       100_000,
    "normal":     200_000,
    "strong":     500_000,
    "paranoid": 1_000_000,
}
DEFAULT_STRENGTH: str = "normal"


def resolve_strength(strength: str) -> int:
    """Return the iteration count for a named strength level.

    Raises ValueError on unknown strength.
    """
    if not isinstance(strength, str):
        raise TypeError("strength must be a str")
    try:
        return STRENGTH_ITERATIONS[strength]
    except KeyError as exc:
        known = ", ".join(sorted(STRENGTH_ITERATIONS))
        raise ValueError(
            f"unknown strength '{strength}'. Known: {known}"
        ) from exc


def generate_salt(length: int = SALT_LEN) -> bytes:
    """Return a cryptographically secure random salt."""
    if length <= 0:
        raise ValueError("salt length must be positive")
    return secrets.token_bytes(length)


def derive_keys(
    passphrase: str,
    salt: bytes,
    iterations: int = DEFAULT_ITERATIONS,
) -> Tuple[bytes, bytes]:
    """Derive (cipher_key, hmac_key) from passphrase and salt.

    Returns a tuple of two 32-byte keys.
    """
    if not isinstance(passphrase, str):
        raise TypeError("passphrase must be a str")
    if not passphrase:
        raise ValueError("passphrase must not be empty")
    if not isinstance(salt, (bytes, bytearray)):
        raise TypeError("salt must be bytes")
    if len(salt) < 8:
        raise ValueError("salt must be at least 8 bytes")
    if iterations < 1:
        raise ValueError("iterations must be >= 1")

    passphrase_bytes = passphrase.encode("utf-8")
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        passphrase_bytes,
        bytes(salt),
        iterations,
        dklen=DK_LEN,
    )
    cipher_key = dk[:CIPHER_KEY_LEN]
    hmac_key = dk[CIPHER_KEY_LEN:CIPHER_KEY_LEN + HMAC_KEY_LEN]
    return cipher_key, hmac_key
