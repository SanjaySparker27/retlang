"""Tests for the named strength levels and iteration-count resolution."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from retlang import encrypt, decrypt  # noqa: E402
from retlang.cipher import _resolve_iterations  # noqa: E402
from retlang.header import parse_envelope  # noqa: E402
from retlang.keyderivation import (  # noqa: E402
    DEFAULT_STRENGTH,
    STRENGTH_ITERATIONS,
    resolve_strength,
)
from retlang.layers.alphabet import decode_bytes  # noqa: E402


PASSPHRASE = "strength-tests"


def _iteration_count_in_header(ciphertext: str, alphabet: str = "base64") -> int:
    """Peel the envelope off a ciphertext and read its iteration count."""
    raw = decode_bytes(ciphertext, alphabet)
    header, _, _ = parse_envelope(raw)
    return header.iterations


class StrengthMapTests(unittest.TestCase):
    def test_four_named_levels_exist(self) -> None:
        self.assertEqual(
            set(STRENGTH_ITERATIONS),
            {"fast", "normal", "strong", "paranoid"},
        )

    def test_expected_iteration_counts(self) -> None:
        self.assertEqual(STRENGTH_ITERATIONS["fast"],       100_000)
        self.assertEqual(STRENGTH_ITERATIONS["normal"],     200_000)
        self.assertEqual(STRENGTH_ITERATIONS["strong"],     500_000)
        self.assertEqual(STRENGTH_ITERATIONS["paranoid"], 1_000_000)

    def test_default_strength_is_normal(self) -> None:
        self.assertEqual(DEFAULT_STRENGTH, "normal")

    def test_resolve_strength(self) -> None:
        for level, expected in STRENGTH_ITERATIONS.items():
            with self.subTest(level=level):
                self.assertEqual(resolve_strength(level), expected)

    def test_resolve_strength_unknown(self) -> None:
        with self.assertRaises(ValueError):
            resolve_strength("bogus")

    def test_resolve_paranoid_without_running_pbkdf2(self) -> None:
        # This verifies the paranoid mapping without actually spending
        # the ~seconds it would take to run PBKDF2 one million times.
        self.assertEqual(resolve_strength("paranoid"), 1_000_000)


class ResolveIterationsTests(unittest.TestCase):
    def test_default_when_neither_given(self) -> None:
        self.assertEqual(
            _resolve_iterations(None, None),
            STRENGTH_ITERATIONS[DEFAULT_STRENGTH],
        )

    def test_strength_resolves(self) -> None:
        self.assertEqual(_resolve_iterations(None, "fast"), 100_000)
        self.assertEqual(_resolve_iterations(None, "strong"), 500_000)
        self.assertEqual(_resolve_iterations(None, "paranoid"), 1_000_000)

    def test_iterations_override(self) -> None:
        self.assertEqual(_resolve_iterations(42_000, None), 42_000)

    def test_both_raises(self) -> None:
        with self.assertRaises(ValueError):
            _resolve_iterations(100_000, "fast")

    def test_bad_iterations_rejected(self) -> None:
        with self.assertRaises(ValueError):
            _resolve_iterations(0, None)
        with self.assertRaises(TypeError):
            _resolve_iterations("100000", None)  # type: ignore[arg-type]

    def test_bad_strength_rejected(self) -> None:
        with self.assertRaises(ValueError):
            _resolve_iterations(None, "medium")


class EncryptHeaderIterationsTests(unittest.TestCase):
    """Verify the header records the resolved iteration count.

    We use the fast strength (100_000) on tiny plaintexts so the full
    test suite stays under ~10 seconds. The paranoid level is NOT
    exercised via a full encrypt -- it is validated via resolve_strength
    above.
    """

    def test_default_is_normal_iterations_in_header(self) -> None:
        ct = encrypt("hi", PASSPHRASE)  # no strength, no iterations
        self.assertEqual(
            _iteration_count_in_header(ct),
            STRENGTH_ITERATIONS["normal"],
        )

    def test_fast_strength_in_header(self) -> None:
        ct = encrypt("hi", PASSPHRASE, strength="fast")
        self.assertEqual(
            _iteration_count_in_header(ct),
            STRENGTH_ITERATIONS["fast"],
        )

    def test_explicit_iterations_in_header(self) -> None:
        ct = encrypt("hi", PASSPHRASE, iterations=12_345)
        self.assertEqual(_iteration_count_in_header(ct), 12_345)

    def test_both_iterations_and_strength_rejected(self) -> None:
        with self.assertRaises(ValueError):
            encrypt("hi", PASSPHRASE, iterations=100_000, strength="fast")

    def test_decrypt_reads_iterations_from_header(self) -> None:
        # Decrypt without the caller knowing the original strength.
        ct = encrypt("payload", PASSPHRASE, strength="fast")
        pt = decrypt(ct, PASSPHRASE)
        self.assertEqual(pt, "payload")


if __name__ == "__main__":
    unittest.main()
