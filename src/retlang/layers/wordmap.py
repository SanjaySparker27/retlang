"""Optional wordmap layer.

Replaces whole-word matches in the plaintext with user-supplied code words.
The operation is reversible when the mapping is bijective (no duplicate
code words). Matching is case-insensitive; the original surrounding
whitespace and punctuation are preserved because we only substitute the
word tokens themselves.

We split the text on a regex that captures whole word-boundaries so that
punctuation and whitespace are retained verbatim between tokens. "Words"
are sequences of unicode word characters; anything else is a separator
and left untouched.
"""

from __future__ import annotations

import re
from typing import Dict, Optional


_TOKEN_RE = re.compile(r"(\w+)", flags=re.UNICODE)


def _build_lookup(mapping: Dict[str, str]) -> Dict[str, str]:
    """Normalize keys to lowercase for case-insensitive matching."""
    lookup: Dict[str, str] = {}
    for key, value in mapping.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise TypeError("wordmap keys and values must be strings")
        if not key:
            raise ValueError("wordmap keys must be non-empty")
        lowered = key.lower()
        if lowered in lookup and lookup[lowered] != value:
            raise ValueError(f"wordmap has conflicting entries for '{key}' (case-insensitive)")
        lookup[lowered] = value
    return lookup


def _invert(mapping: Dict[str, str]) -> Dict[str, str]:
    """Invert the mapping (code word -> original word).

    Case-insensitive on the code word side. Raises ValueError if the
    mapping is not bijective (two originals would map to the same code word).
    """
    inverted: Dict[str, str] = {}
    for original, code in mapping.items():
        if not isinstance(code, str) or not code:
            raise ValueError("wordmap values must be non-empty strings")
        code_lower = code.lower()
        if code_lower in inverted and inverted[code_lower] != original:
            raise ValueError(
                f"wordmap is not bijective: code word '{code}' maps to multiple originals"
            )
        inverted[code_lower] = original
    return inverted


def apply_wordmap(text: str, mapping: Optional[Dict[str, str]]) -> str:
    """Replace whole words in `text` per the mapping.

    Case-insensitive matching. Whitespace and punctuation are preserved.
    If `mapping` is None or empty, returns text unchanged.
    """
    if not mapping:
        return text
    if not isinstance(text, str):
        raise TypeError("text must be a str")
    lookup = _build_lookup(mapping)

    def _sub(match: re.Match) -> str:
        word = match.group(1)
        replacement = lookup.get(word.lower())
        return replacement if replacement is not None else word

    return _TOKEN_RE.sub(_sub, text)


def reverse_wordmap(text: str, mapping: Optional[Dict[str, str]]) -> str:
    """Reverse the substitution applied by apply_wordmap.

    Requires the mapping to be bijective (no two originals map to the
    same code word, case-insensitively).
    """
    if not mapping:
        return text
    if not isinstance(text, str):
        raise TypeError("text must be a str")
    inverted = _invert(mapping)

    def _sub(match: re.Match) -> str:
        word = match.group(1)
        replacement = inverted.get(word.lower())
        return replacement if replacement is not None else word

    return _TOKEN_RE.sub(_sub, text)
