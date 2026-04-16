"""retlang: two-way tamper-evident secret-language encryption.

Public API:
    encrypt(plaintext, passphrase, *, alphabet="base64", wordmap=None,
            iterations=None, strength=None) -> str
    decrypt(ciphertext, passphrase, *, alphabet="base64", wordmap=None) -> str

    share(plaintext, passphrase, *, wordmap=None, strength="normal") -> str
        Produces a retlang:// URL containing the raw envelope bytes.
    open_url(url, passphrase, *, wordmap=None) -> str
        Reverse of share().

    suggest_phrase(words=6, separator="-") -> str
        Diceware-style passphrase from the bundled EFF wordlist.
    score_passphrase(passphrase) -> dict
        Heuristic strength scorer (bits, score, verdict, notes).

Either `iterations` (explicit int) or `strength` (one of "fast", "normal",
"strong", "paranoid") may be passed to encrypt(), but not both.
"""

from .cipher import DEFAULT_STRENGTH, STRENGTH_ITERATIONS, decrypt, encrypt
from .entropy import score as score_passphrase
from .phrase import suggest_phrase
from .share import open_url, share

__version__ = "0.2.0"

__all__ = [
    "encrypt",
    "decrypt",
    "share",
    "open_url",
    "suggest_phrase",
    "score_passphrase",
    "STRENGTH_ITERATIONS",
    "DEFAULT_STRENGTH",
    "__version__",
]
