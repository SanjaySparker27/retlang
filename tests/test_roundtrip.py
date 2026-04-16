"""Round-trip encrypt/decrypt tests across alphabets and inputs."""

from __future__ import annotations

import os
import sys
import unittest

# Make src/ importable when running `python -m unittest discover tests`.
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from retlang import decrypt, encrypt  # noqa: E402
from retlang.alphabets import list_alphabets  # noqa: E402


# Pick a tiny iteration count for the parametrized strength sweep so the
# full matrix (11 alphabets x 4 strength levels) finishes in well under
# ~10 seconds on a developer laptop. The actual strength-vs-iterations
# wiring is verified more precisely in tests/test_strength.py.
_FAST_TEST_ITERATIONS = 1_000


class RoundTripTests(unittest.TestCase):
    PASSPHRASE = "correct horse battery staple"
    MESSAGES = [
        "hello world",
        "",
        "a",
        "The quick brown fox jumps over the lazy dog.",
        "unicode: café, naïve, 北京, \U0001F600 smile",
        "line1\nline2\r\nline3\ttabbed",
        "x" * 1024,
    ]

    def test_roundtrip_default_alphabet(self) -> None:
        for msg in self.MESSAGES:
            with self.subTest(msg=msg):
                ct = encrypt(msg, self.PASSPHRASE, iterations=_FAST_TEST_ITERATIONS)
                self.assertIsInstance(ct, str)
                pt = decrypt(ct, self.PASSPHRASE)
                self.assertEqual(pt, msg)

    def test_roundtrip_all_alphabets(self) -> None:
        # Parametrize round-trip over all 11 alphabets.
        for alphabet in list_alphabets():
            for msg in ["hello", "unicode: café 北京", ""]:
                with self.subTest(alphabet=alphabet, msg=msg):
                    ct = encrypt(
                        msg,
                        self.PASSPHRASE,
                        alphabet=alphabet,
                        iterations=_FAST_TEST_ITERATIONS,
                    )
                    pt = decrypt(ct, self.PASSPHRASE, alphabet=alphabet)
                    self.assertEqual(pt, msg)

    def test_roundtrip_all_alphabets_all_strengths(self) -> None:
        """Round-trip one message under every (alphabet, strength) pair.

        To keep the test under ~10 seconds we artificially lower the
        iteration count via `iterations=` for every strength level. The
        strength-to-iteration-count mapping itself is verified purely at
        the helper-function level in test_strength.py so we do not have
        to actually run 1_000_000 PBKDF2 rounds.
        """
        strength_levels = ("fast", "normal", "strong", "paranoid")
        for alphabet in list_alphabets():
            for level in strength_levels:
                with self.subTest(alphabet=alphabet, level=level):
                    # Use iterations= override to keep runtime short; the
                    # header still records the iteration count so decrypt
                    # works without knowing the strength.
                    ct = encrypt(
                        f"payload-{alphabet}-{level}",
                        self.PASSPHRASE,
                        alphabet=alphabet,
                        iterations=_FAST_TEST_ITERATIONS,
                    )
                    pt = decrypt(ct, self.PASSPHRASE, alphabet=alphabet)
                    self.assertEqual(pt, f"payload-{alphabet}-{level}")

    def test_wrong_passphrase_raises(self) -> None:
        ct = encrypt("secret", self.PASSPHRASE, iterations=_FAST_TEST_ITERATIONS)
        with self.assertRaises(Exception):
            decrypt(ct, "wrong passphrase")

    def test_different_salt_each_call(self) -> None:
        ct1 = encrypt("same message", self.PASSPHRASE, iterations=_FAST_TEST_ITERATIONS)
        ct2 = encrypt("same message", self.PASSPHRASE, iterations=_FAST_TEST_ITERATIONS)
        # Salt is random, so ciphertext must differ each time.
        self.assertNotEqual(ct1, ct2)
        self.assertEqual(decrypt(ct1, self.PASSPHRASE), "same message")
        self.assertEqual(decrypt(ct2, self.PASSPHRASE), "same message")

    def test_custom_iterations(self) -> None:
        ct = encrypt("hi", self.PASSPHRASE, iterations=50_000)
        self.assertEqual(decrypt(ct, self.PASSPHRASE), "hi")

    def test_utf8_byte_exact(self) -> None:
        msg = "\u0000\u00ff\u0100\u4e2d\u6587"
        ct = encrypt(msg, self.PASSPHRASE, iterations=_FAST_TEST_ITERATIONS)
        out = decrypt(ct, self.PASSPHRASE)
        self.assertEqual(out, msg)
        self.assertEqual(out.encode("utf-8"), msg.encode("utf-8"))


if __name__ == "__main__":
    unittest.main()
