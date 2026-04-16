"""Diceware-style passphrase suggestion.

Uses `secrets.SystemRandom()` (CSPRNG) to pick N words uniformly at
random from the bundled EFF large wordlist (7776 words, ~12.9 bits of
entropy per word).

The wordlist is loaded lazily on first use and cached in-process. It is
shipped as `src/retlang/wordlists/eff_large.txt`, one word per line.
"""

from __future__ import annotations

import math
import secrets
from pathlib import Path
from typing import List, Optional, Tuple

# Cached wordlist tuple. Populated on first call.
_WORDLIST: Optional[Tuple[str, ...]] = None
# Reusable CSPRNG (secrets.SystemRandom() wraps os.urandom).
_RNG = secrets.SystemRandom()

# Minimum required wordlist size. Below 4096 words the per-word entropy
# falls under 12 bits which is not acceptable for diceware phrases.
_MIN_WORDS = 4096


def _wordlist_path() -> Path:
    """Return the on-disk path of the bundled wordlist."""
    return Path(__file__).parent / "wordlists" / "eff_large.txt"


def _load_wordlist() -> Tuple[str, ...]:
    """Read the wordlist once and cache the result.

    Raises RuntimeError if the bundled file is missing or too small.
    """
    global _WORDLIST
    if _WORDLIST is not None:
        return _WORDLIST
    path = _wordlist_path()
    if not path.is_file():
        raise RuntimeError(
            f"wordlist not found at {path}. "
            "retlang is installed incorrectly."
        )
    words: List[str] = []
    seen = set()
    with path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            word = raw.strip()
            if not word or word.startswith("#"):
                continue
            # Accept "digits<whitespace>word" (EFF format) or bare word.
            parts = word.split()
            candidate = parts[-1]
            if not candidate.isascii() or not candidate.isalpha():
                # Skip anything that is not a plain ascii alpha word.
                continue
            candidate = candidate.lower()
            if candidate in seen:
                continue
            seen.add(candidate)
            words.append(candidate)
    if len(words) < _MIN_WORDS:
        raise RuntimeError(
            f"wordlist at {path} has {len(words)} usable words; "
            f"need at least {_MIN_WORDS}"
        )
    _WORDLIST = tuple(words)
    return _WORDLIST


def wordlist_size() -> int:
    """Return the number of words in the bundled wordlist."""
    return len(_load_wordlist())


def suggest_phrase(words: int = 6, separator: str = "-") -> str:
    """Return a diceware-style passphrase of `words` words.

    Uses `secrets.choice()` for each pick. `words` must be >= 1.
    """
    if not isinstance(words, int) or isinstance(words, bool):
        raise TypeError("words must be an int")
    if words < 1:
        raise ValueError("words must be >= 1")
    if not isinstance(separator, str):
        raise TypeError("separator must be a str")
    pool = _load_wordlist()
    # Per requirement: use secrets.choice (module-level, CSPRNG-backed).
    picked = [secrets.choice(pool) for _ in range(words)]
    return separator.join(picked)


def phrase_entropy_bits(words: int, wordlist_size_value: int) -> float:
    """Return the total entropy in bits of a diceware phrase.

    Formula: words * log2(wordlist_size_value). Both inputs must be positive.
    """
    if not isinstance(words, int) or isinstance(words, bool):
        raise TypeError("words must be an int")
    if not isinstance(wordlist_size_value, int) or isinstance(
        wordlist_size_value, bool
    ):
        raise TypeError("wordlist_size_value must be an int")
    if words < 1:
        raise ValueError("words must be >= 1")
    if wordlist_size_value < 2:
        raise ValueError("wordlist_size_value must be >= 2")
    return words * math.log2(wordlist_size_value)


__all__ = [
    "suggest_phrase",
    "phrase_entropy_bits",
    "wordlist_size",
]
