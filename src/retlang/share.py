"""retlang:// URL format for one-click sharing.

A retlang URL wraps the raw binary envelope (header + ciphertext + HMAC)
as url-safe base64 with the prefix `retlang://v1/`. This is a wire format
independent of the visual alphabet profile -- it is intended for copy /
paste into chat apps, QR codes, and the clipboard-watcher agent.

Public API
----------
- RETLANG_URL_PREFIX   constant prefix string
- make_url(bytes)      pack raw envelope bytes into a retlang:// URL
- parse_url(str)       reverse of make_url; raises ValueError on malformed
- is_retlang_url(str)  cheap regex-level check
- share(...)           high-level: encrypt then wrap in URL
- open_url(...)        high-level: unwrap URL then decrypt
"""

from __future__ import annotations

import base64
import re
from typing import Dict, Optional

from .alphabets import alphabet_id
from .header import Header, envelope_body, VERSION as HEADER_VERSION
from .integrity import compute_tag, verify_tag
from .keyderivation import derive_keys, generate_salt
from .layers import (
    apply_wordmap,
    reverse_wordmap,
    vigenere_decrypt,
    vigenere_encrypt,
)
from .header import parse_envelope
from .cipher import _resolve_iterations

RETLANG_URL_PREFIX: str = "retlang://v1/"

# A retlang URL body is url-safe base64 (A-Z a-z 0-9 - _) plus optional
# "=" padding. Length must be > 0.
_URL_RE = re.compile(
    r"^retlang://v1/([A-Za-z0-9_\-]+=*)$"
)


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(bytes(data)).decode("ascii")


def _b64url_decode(text: str) -> bytes:
    # Accept input with or without padding; pad up to multiple of 4.
    padded = text + "=" * ((4 - len(text) % 4) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def make_url(envelope_bytes: bytes) -> str:
    """Wrap raw envelope bytes as a retlang:// URL."""
    if not isinstance(envelope_bytes, (bytes, bytearray)):
        raise TypeError("envelope_bytes must be bytes")
    if len(envelope_bytes) == 0:
        raise ValueError("envelope_bytes must not be empty")
    return RETLANG_URL_PREFIX + _b64url_encode(envelope_bytes)


def parse_url(url: str) -> bytes:
    """Unwrap a retlang:// URL and return the raw envelope bytes.

    Raises ValueError on malformed input.
    """
    if not isinstance(url, str):
        raise TypeError("url must be a str")
    text = url.strip()
    match = _URL_RE.match(text)
    if not match:
        raise ValueError(
            "malformed retlang URL: expected retlang://v1/<urlsafe-base64>"
        )
    body = match.group(1)
    try:
        raw = _b64url_decode(body)
    except Exception as exc:
        raise ValueError(f"malformed retlang URL body: {exc}") from exc
    if len(raw) == 0:
        raise ValueError("retlang URL decoded to empty envelope")
    return raw


def is_retlang_url(text: str) -> bool:
    """Return True if `text` looks like a retlang:// URL (cheap regex check)."""
    if not isinstance(text, str):
        return False
    return bool(_URL_RE.match(text.strip()))


def share(
    plaintext: str,
    passphrase: str,
    *,
    wordmap: Optional[Dict[str, str]] = None,
    strength: Optional[str] = "normal",
    iterations: Optional[int] = None,
) -> str:
    """Encrypt `plaintext` and return a retlang:// URL.

    The URL encodes the raw envelope bytes directly (not a visual alphabet),
    so it is compact and suitable for QR codes and clipboard transport.
    """
    if not isinstance(plaintext, str):
        raise TypeError("plaintext must be a str")
    if not isinstance(passphrase, str):
        raise TypeError("passphrase must be a str")

    # When both are None, _resolve_iterations picks the default strength.
    # share() defaults strength="normal" so callers get a sane default.
    effective_iterations = _resolve_iterations(iterations, strength)

    transformed = apply_wordmap(plaintext, wordmap)
    plain_bytes = transformed.encode("utf-8")

    salt = generate_salt()
    cipher_key, hmac_key = derive_keys(
        passphrase, salt, iterations=effective_iterations
    )
    ciphertext = vigenere_encrypt(plain_bytes, cipher_key)

    header = Header(
        version=HEADER_VERSION,
        iterations=effective_iterations,
        salt=salt,
        # URLs are alphabet-agnostic; store base64 id for round-trip sanity.
        alphabet_id=alphabet_id("base64"),
    )
    body = envelope_body(header, ciphertext)
    tag = compute_tag(hmac_key, body)
    envelope = body + tag
    return make_url(envelope)


def open_url(
    url: str,
    passphrase: str,
    *,
    wordmap: Optional[Dict[str, str]] = None,
) -> str:
    """Decrypt a retlang:// URL produced by `share()`."""
    if not isinstance(passphrase, str):
        raise TypeError("passphrase must be a str")

    raw = parse_url(url)
    header, cipher_bytes, tag = parse_envelope(raw)

    cipher_key, hmac_key = derive_keys(
        passphrase, header.salt, iterations=header.iterations
    )

    body = envelope_body(header, cipher_bytes)
    verify_tag(hmac_key, body, tag)

    plain_bytes = vigenere_decrypt(cipher_bytes, cipher_key)
    try:
        transformed = plain_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("decrypted bytes are not valid UTF-8") from exc

    return reverse_wordmap(transformed, wordmap)


__all__ = [
    "RETLANG_URL_PREFIX",
    "make_url",
    "parse_url",
    "is_retlang_url",
    "share",
    "open_url",
]
