"""retlang: two-way tamper-evident secret-language encryption.

Public API:
    encrypt(plaintext, passphrase, *, alphabet="base64", wordmap=None,
            iterations=None, strength=None) -> str
    decrypt(ciphertext, passphrase, *, alphabet="base64", wordmap=None) -> str

Either `iterations` (explicit int) or `strength` (one of "fast", "normal",
"strong", "paranoid") may be passed to encrypt(), but not both.
"""

from .cipher import DEFAULT_STRENGTH, STRENGTH_ITERATIONS, decrypt, encrypt

__version__ = "0.1.0"

__all__ = [
    "encrypt",
    "decrypt",
    "STRENGTH_ITERATIONS",
    "DEFAULT_STRENGTH",
    "__version__",
]
