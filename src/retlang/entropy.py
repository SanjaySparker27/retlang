"""Passphrase strength scorer (pure stdlib).

Given a passphrase string, produce a dict with:
    bits     estimated Shannon entropy (float)
    score    normalized 0..100 integer
    verdict  one of "weak" | "ok" | "good" | "strong" | "excellent"
    notes    list of human-readable explanations / suggestions

This is a heuristic: we compute the search-space bits (log2 of the pool
cardinality times length), add a Shannon-entropy term based on actual
character frequencies, and apply penalties for short length and dictionary
words. No ML model, no external data aside from a tiny top-N English
blacklist.
"""

from __future__ import annotations

import math
import re
import string
from typing import Dict, List

# Character-class pool sizes mirror the classic search-space model.
_LOWER = set(string.ascii_lowercase)
_UPPER = set(string.ascii_uppercase)
_DIGITS = set(string.digits)
_SYMBOLS = set(string.punctuation)

# Very short, curated blacklist of obviously-bad passphrases. Not intended
# to catch everything -- just the worst offenders.
_COMMON = frozenset(
    {
        "password", "passw0rd", "123456", "12345678", "qwerty",
        "letmein", "admin", "welcome", "iloveyou", "monkey",
        "dragon", "master", "abc123", "trustno1", "sunshine",
        "p@ssword", "password1", "000000", "111111", "1q2w3e4r",
        "qwertyuiop", "zaq12wsx", "baseball", "football", "superman",
        "test", "hello", "hello123", "princess", "access",
    }
)


def _char_pool_size(pw: str) -> int:
    pool = 0
    chars = set(pw)
    if chars & _LOWER:
        pool += 26
    if chars & _UPPER:
        pool += 26
    if chars & _DIGITS:
        pool += 10
    if chars & _SYMBOLS:
        pool += len(_SYMBOLS)
    # Any non-ASCII codepoints expand the pool generously.
    extra = {c for c in chars if ord(c) > 127}
    if extra:
        pool += max(len(extra) * 4, 32)
    return max(pool, 1)


def _shannon_bits(pw: str) -> float:
    if not pw:
        return 0.0
    freq: Dict[str, int] = {}
    for ch in pw:
        freq[ch] = freq.get(ch, 0) + 1
    total = len(pw)
    h = 0.0
    for count in freq.values():
        p = count / total
        h -= p * math.log2(p)
    # Multiply per-char entropy by length to get total bits for this string.
    return h * total


def _looks_like_diceware(pw: str) -> bool:
    """Heuristic: 3+ ascii-alpha tokens joined by `-`, `_`, ` ` or `.`."""
    tokens = re.split(r"[-_.\s]+", pw.strip())
    tokens = [t for t in tokens if t]
    if len(tokens) < 3:
        return False
    return all(t.isascii() and t.isalpha() and len(t) >= 2 for t in tokens)


def score(passphrase: str) -> Dict[str, object]:
    """Return {"bits","score","verdict","notes"} for `passphrase`."""
    if not isinstance(passphrase, str):
        raise TypeError("passphrase must be a str")

    notes: List[str] = []
    length = len(passphrase)

    if length == 0:
        return {
            "bits": 0.0,
            "score": 0,
            "verdict": "weak",
            "notes": ["empty passphrase"],
        }

    pool = _char_pool_size(passphrase)
    # Search-space bits: length * log2(pool).
    search_bits = length * math.log2(pool)
    shannon_bits = _shannon_bits(passphrase)
    # Blend: take the minimum so a long string of the same char does not
    # score high just because the pool is large.
    bits = min(search_bits, shannon_bits)

    if length < 8:
        notes.append(
            f"short ({length} chars); aim for 12+ chars or 4+ diceware words"
        )
        bits *= 0.6

    if passphrase.lower() in _COMMON:
        notes.append("appears in common-password blacklist")
        bits = min(bits, 10.0)

    if _looks_like_diceware(passphrase):
        notes.append("looks like a diceware passphrase (good)")
        # Diceware strings get the benefit of the doubt: don't penalize
        # their limited character pool.
        bits = max(bits, search_bits * 0.9)

    # Character-class coverage hints.
    classes_present = sum(
        bool(set(passphrase) & klass)
        for klass in (_LOWER, _UPPER, _DIGITS, _SYMBOLS)
    )
    if classes_present < 2 and not _looks_like_diceware(passphrase):
        notes.append("uses only one character class; add variety")

    # Normalize 0..100. Anything >= 128 bits saturates.
    normalized = max(0.0, min(1.0, bits / 128.0))
    score_val = int(round(normalized * 100))

    if bits < 28:
        verdict = "weak"
    elif bits < 48:
        verdict = "ok"
    elif bits < 72:
        verdict = "good"
    elif bits < 100:
        verdict = "strong"
    else:
        verdict = "excellent"

    if not notes:
        notes.append("no obvious weaknesses detected")

    return {
        "bits": round(bits, 2),
        "score": score_val,
        "verdict": verdict,
        "notes": notes,
    }


def format_report(passphrase: str) -> str:
    """Return a multi-line human-readable strength report."""
    result = score(passphrase)
    lines = [
        "retlang passphrase strength report",
        "----------------------------------",
        f"length   : {len(passphrase)} chars",
        f"bits     : {result['bits']}",
        f"score    : {result['score']}/100",
        f"verdict  : {result['verdict']}",
        "notes    :",
    ]
    for note in result["notes"]:
        lines.append(f"  - {note}")
    return "\n".join(lines) + "\n"


__all__ = ["score", "format_report"]
