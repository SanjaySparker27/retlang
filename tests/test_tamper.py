"""Tamper-detection tests: flipping bits must cause HMAC verification to fail."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from retlang import decrypt, encrypt  # noqa: E402
from retlang.alphabets import alphabet_symbols  # noqa: E402
from retlang.integrity import IntegrityError  # noqa: E402
from retlang.layers.alphabet import decode_bytes, encode_bytes  # noqa: E402


PASSPHRASE = "p@ssw0rd-test"
MESSAGE = "top secret message"


def _flip_byte(raw: bytes, index: int) -> bytes:
    out = bytearray(raw)
    out[index] ^= 0x01
    return bytes(out)


class TamperTests(unittest.TestCase):
    def test_flip_in_ciphertext_region_rejected(self) -> None:
        ct = encrypt(MESSAGE, PASSPHRASE, alphabet="base64")
        raw = decode_bytes(ct, "base64")
        # Header is 26 bytes, tag is 32 bytes at end. Flip a byte in the
        # ciphertext region, which is between those.
        self.assertGreater(len(raw), 26 + 32)
        tampered = _flip_byte(raw, 26 + 1)
        tampered_ct = encode_bytes(tampered, "base64")
        with self.assertRaises((IntegrityError, ValueError)):
            decrypt(tampered_ct, PASSPHRASE, alphabet="base64")

    def test_flip_in_header_rejected(self) -> None:
        ct = encrypt(MESSAGE, PASSPHRASE)
        raw = decode_bytes(ct, "base64")
        # Flip a byte in the salt region (index 9..25).
        tampered = _flip_byte(raw, 12)
        tampered_ct = encode_bytes(tampered, "base64")
        with self.assertRaises((IntegrityError, ValueError)):
            decrypt(tampered_ct, PASSPHRASE)

    def test_flip_in_tag_rejected(self) -> None:
        ct = encrypt(MESSAGE, PASSPHRASE)
        raw = decode_bytes(ct, "base64")
        tampered = _flip_byte(raw, len(raw) - 1)
        tampered_ct = encode_bytes(tampered, "base64")
        with self.assertRaises((IntegrityError, ValueError)):
            decrypt(tampered_ct, PASSPHRASE)

    def test_truncated_envelope_rejected(self) -> None:
        ct = encrypt(MESSAGE, PASSPHRASE)
        raw = decode_bytes(ct, "base64")
        truncated_ct = encode_bytes(raw[:20], "base64")
        with self.assertRaises((IntegrityError, ValueError)):
            decrypt(truncated_ct, PASSPHRASE)

    def test_alphabet_substitution_fails_hmac(self) -> None:
        # Encrypt with one alphabet, try to decode with another (same
        # underlying bytes would decode differently, making HMAC fail).
        ct = encrypt(MESSAGE, PASSPHRASE, alphabet="emoji")
        with self.assertRaises((IntegrityError, ValueError)):
            decrypt(ct, PASSPHRASE, alphabet="base64")

    def test_swap_two_ciphertext_chars_rejected(self) -> None:
        ct = encrypt(MESSAGE, PASSPHRASE, alphabet="geometric")
        symbols = alphabet_symbols("geometric")
        # Find first character in ct that is a geometric symbol and swap
        # it with a different one. Because decode_bytes may choke on
        # invalid unicode, we replace one valid symbol with another.
        chars = list(ct)
        swap_done = False
        for idx, ch in enumerate(chars):
            if ch in symbols:
                replacement = symbols[0] if ch != symbols[0] else symbols[1]
                chars[idx] = replacement
                swap_done = True
                break
        self.assertTrue(swap_done)
        tampered_ct = "".join(chars)
        with self.assertRaises((IntegrityError, ValueError)):
            decrypt(tampered_ct, PASSPHRASE, alphabet="geometric")


if __name__ == "__main__":
    unittest.main()
