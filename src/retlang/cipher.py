"""High-level encrypt / decrypt pipeline.

Pipeline (encrypt):
    1. Derive 64 bytes (cipher_key + hmac_key) via PBKDF2-HMAC-SHA256.
    2. Apply optional wordmap substitution to the plaintext.
    3. UTF-8 encode the result.
    4. Vigenere-shift the bytes with the cipher key.
    5. Build envelope: MAGIC | VERSION | ITER | SALT | ALPHABET_ID | CIPHERTEXT
    6. HMAC-SHA256 the envelope with hmac_key; append the 32-byte tag.
    7. Encode the full binary blob using the chosen alphabet profile.

Decrypt reverses the above and verifies the HMAC in constant time before
touching any ciphertext bytes.
"""

from __future__ import annotations

from typing import Dict, Optional

from .alphabets import alphabet_id, name_from_id
from .header import VERSION as HEADER_VERSION, Header, envelope_body, parse_envelope
from .integrity import compute_tag, verify_tag
from .keyderivation import (
    DEFAULT_STRENGTH,
    STRENGTH_ITERATIONS,
    derive_keys,
    generate_salt,
    resolve_strength,
)
from .layers import (
    apply_wordmap,
    decode_bytes,
    encode_bytes,
    reverse_wordmap,
    vigenere_decrypt,
    vigenere_encrypt,
)


def _resolve_iterations(
    iterations: Optional[int],
    strength: Optional[str],
) -> int:
    """Resolve the effective iteration count from (iterations, strength).

    Rules:
    * If both are given, raise ValueError.
    * If only iterations is given, use it directly (must be >= 1).
    * If only strength is given, look it up in STRENGTH_ITERATIONS.
    * If neither is given, use the default strength.
    """
    if iterations is not None and strength is not None:
        raise ValueError(
            "pass either 'iterations' or 'strength', not both"
        )
    if iterations is not None:
        if not isinstance(iterations, int) or isinstance(iterations, bool):
            raise TypeError("iterations must be an int")
        if iterations < 1:
            raise ValueError("iterations must be >= 1")
        return iterations
    if strength is None:
        strength = DEFAULT_STRENGTH
    return resolve_strength(strength)


def encrypt(
    plaintext: str,
    passphrase: str,
    *,
    alphabet: str = "base64",
    wordmap: Optional[Dict[str, str]] = None,
    iterations: Optional[int] = None,
    strength: Optional[str] = None,
) -> str:
    """Encrypt `plaintext` with `passphrase` and return a string ciphertext.

    Either `iterations` (explicit int) or `strength` (named level in
    STRENGTH_ITERATIONS) may be passed, but not both. When neither is
    given the default strength ("normal") is used.
    """
    if not isinstance(plaintext, str):
        raise TypeError("plaintext must be a str")
    if not isinstance(passphrase, str):
        raise TypeError("passphrase must be a str")

    effective_iterations = _resolve_iterations(iterations, strength)

    # Step 2: wordmap substitution (optional).
    transformed = apply_wordmap(plaintext, wordmap)

    # Step 3: UTF-8 encode.
    plain_bytes = transformed.encode("utf-8")

    # Step 1: derive keys.
    salt = generate_salt()
    cipher_key, hmac_key = derive_keys(
        passphrase, salt, iterations=effective_iterations
    )

    # Step 4: Vigenere byte shift.
    ciphertext = vigenere_encrypt(plain_bytes, cipher_key)

    # Step 5: build header.
    header = Header(
        version=HEADER_VERSION,
        iterations=effective_iterations,
        salt=salt,
        alphabet_id=alphabet_id(alphabet),
    )
    body = envelope_body(header, ciphertext)

    # Step 6: HMAC tag.
    tag = compute_tag(hmac_key, body)
    envelope = body + tag

    # Step 7: encode with the named alphabet.
    return encode_bytes(envelope, alphabet)


def decrypt(
    ciphertext: str,
    passphrase: str,
    *,
    alphabet: str = "base64",
    wordmap: Optional[Dict[str, str]] = None,
) -> str:
    """Decrypt `ciphertext` produced by encrypt(). Returns the original plaintext."""
    if not isinstance(ciphertext, str):
        raise TypeError("ciphertext must be a str")
    if not isinstance(passphrase, str):
        raise TypeError("passphrase must be a str")

    raw = decode_bytes(ciphertext, alphabet)
    header, cipher_bytes, tag = parse_envelope(raw)

    # Sanity check that header's alphabet matches decoder choice; if not,
    # we still proceed -- the alphabet selection only affects string
    # encoding, not the raw bytes.
    expected_name = name_from_id(header.alphabet_id)
    if expected_name != alphabet:
        raise ValueError(
            f"envelope alphabet '{expected_name}' does not match requested '{alphabet}'"
        )

    cipher_key, hmac_key = derive_keys(
        passphrase,
        header.salt,
        iterations=header.iterations,
    )

    # MANDATORY constant-time HMAC verification BEFORE touching ciphertext.
    body = envelope_body(header, cipher_bytes)
    verify_tag(hmac_key, body, tag)

    plain_bytes = vigenere_decrypt(cipher_bytes, cipher_key)
    try:
        transformed = plain_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("decrypted bytes are not valid UTF-8") from exc

    return reverse_wordmap(transformed, wordmap)


# Re-export the strength map so callers can introspect available levels.
__all__ = [
    "encrypt",
    "decrypt",
    "STRENGTH_ITERATIONS",
    "DEFAULT_STRENGTH",
]
