"""Alphabet (base64-style) encoding layer.

Given a 64-symbol alphabet we encode an arbitrary byte string as a string
of those symbols, six bits per symbol. We use the same padding semantics
as classic base64 but emit a per-alphabet pad symbol only when needed.

Under the hood we always run the bytes through stdlib `urlsafe_b64encode`
to get the standard 6-bit grouping + padding, then translate each result
character ('A'..'Z', 'a'..'z', '0'..'9', '-', '_') to the symbol at the
matching index in the target alphabet. This works for every profile,
including those whose symbols are multi-character codes (letters /
numbers) because we concatenate symbols of fixed width.
"""

from __future__ import annotations

import base64
from typing import Dict, Tuple

from ..alphabets import alphabet_profile


# url-safe base64 canonical order matches the `base64` profile exactly.
_URLSAFE_B64: str = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789-_"
)


def _pad_symbol(name: str) -> str:
    """Return the dedicated pad 'symbol' for a given alphabet.

    For profiles whose symbols are printable ASCII we use "=" (the classic
    base64 pad). For profiles with non-ASCII symbols we also use "=" --
    it is guaranteed not to appear in any of our 64-symbol sets.
    """
    return "="


def _translation_tables(name: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Return (encode_table, decode_table) mapping base64-char <-> symbol.

    encode_table maps each char of url-safe base64 to the alphabet symbol
    (which may itself be a multi-character code).
    decode_table maps each alphabet symbol back to the url-safe base64 char.
    """
    profile = alphabet_profile(name)
    encode_table: Dict[str, str] = {}
    decode_table: Dict[str, str] = {}
    for src, dst in zip(_URLSAFE_B64, profile.symbols):
        encode_table[src] = dst
        decode_table[dst] = src
    return encode_table, decode_table


def encode_bytes(data: bytes, alphabet_name: str) -> str:
    """Encode bytes as a string using the given alphabet profile."""
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("data must be bytes")
    encode_table, _ = _translation_tables(alphabet_name)
    pad = _pad_symbol(alphabet_name)
    b64 = base64.urlsafe_b64encode(bytes(data)).decode("ascii")
    out = []
    for ch in b64:
        if ch == "=":
            out.append(pad)
        else:
            out.append(encode_table[ch])
    return "".join(out)


def decode_bytes(text: str, alphabet_name: str) -> bytes:
    """Inverse of encode_bytes.

    Supports alphabets whose symbols are single or multi-character codes:
    we read `width` characters at a time when width > 1.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a str")
    profile = alphabet_profile(alphabet_name)
    _, decode_table = _translation_tables(alphabet_name)
    pad = _pad_symbol(alphabet_name)
    width = profile.width

    # First strip whitespace entirely (permissive).
    filtered = "".join(ch for ch in text if not ch.isspace())

    b64_chars = []
    i = 0
    n = len(filtered)
    while i < n:
        ch = filtered[i]
        if ch == pad:
            b64_chars.append("=")
            i += 1
            continue
        if width == 1:
            try:
                b64_chars.append(decode_table[ch])
            except KeyError as exc:
                raise ValueError(
                    f"character {ch!r} is not valid in alphabet '{alphabet_name}'"
                ) from exc
            i += 1
        else:
            # Multi-char symbol: slurp exactly `width` characters.
            if i + width > n:
                raise ValueError(
                    f"truncated multi-char symbol in alphabet '{alphabet_name}'"
                )
            chunk = filtered[i:i + width]
            try:
                b64_chars.append(decode_table[chunk])
            except KeyError as exc:
                raise ValueError(
                    f"sequence {chunk!r} is not valid in alphabet '{alphabet_name}'"
                ) from exc
            i += width
    b64 = "".join(b64_chars)
    try:
        return base64.urlsafe_b64decode(b64.encode("ascii"))
    except Exception as exc:  # binascii.Error etc.
        raise ValueError(f"malformed encoded text: {exc}") from exc
