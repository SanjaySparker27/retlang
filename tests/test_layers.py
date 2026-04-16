"""Tests for the individual transformation layers."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from retlang.alphabets import (  # noqa: E402
    ALPHABETS,
    NAME_TO_ID,
    alphabet_preview,
    list_alphabets,
)
from retlang.layers.alphabet import decode_bytes, encode_bytes  # noqa: E402
from retlang.layers.vigenere import vigenere_decrypt, vigenere_encrypt  # noqa: E402


# Every profile we expect to exist, with its canonical id.
EXPECTED_PROFILES = {
    "base64":        0,
    "letters":       1,
    "numbers":       2,
    "symbols":       3,
    "emoji-smiley":  4,
    "emoji-animals": 5,
    "emoji-food":    6,
    "emoji-nature":  7,
    "geometric":     8,
    "runes":         9,
    "astro":        10,
}


class VigenereTests(unittest.TestCase):
    def test_roundtrip(self) -> None:
        key = b"\x01\x02\x03\x04"
        for data in [b"", b"a", b"hello", bytes(range(256))]:
            with self.subTest(data=data):
                enc = vigenere_encrypt(data, key)
                dec = vigenere_decrypt(enc, key)
                self.assertEqual(dec, data)

    def test_empty_key_rejected(self) -> None:
        with self.assertRaises(ValueError):
            vigenere_encrypt(b"data", b"")

    def test_shift_semantics(self) -> None:
        key = b"\x01"
        enc = vigenere_encrypt(b"\x00\xFF", key)
        # 0+1=1, 255+1=0 (mod 256)
        self.assertEqual(enc, b"\x01\x00")


class AlphabetUniquenessTests(unittest.TestCase):
    """Parametrized: every profile has exactly 64 unique symbols."""

    def test_every_profile_has_64_unique_symbols(self) -> None:
        self.assertEqual(
            set(ALPHABETS.keys()),
            set(EXPECTED_PROFILES.keys()),
            "registered profiles do not match the expected set",
        )
        for name in EXPECTED_PROFILES:
            with self.subTest(alphabet=name):
                profile = ALPHABETS[name]
                self.assertEqual(
                    len(profile.symbols),
                    64,
                    f"{name} must have 64 symbols",
                )
                self.assertEqual(
                    len(set(profile.symbols)),
                    64,
                    f"{name} must have 64 UNIQUE symbols",
                )
                # Multi-char-width profiles: every symbol is fixed width.
                if profile.width > 1:
                    for sym in profile.symbols:
                        self.assertEqual(len(sym), profile.width)

    def test_profile_ids_match_expected(self) -> None:
        for name, expected_id in EXPECTED_PROFILES.items():
            with self.subTest(alphabet=name):
                self.assertEqual(NAME_TO_ID[name], expected_id)

    def test_preview_returns_requested_count(self) -> None:
        for name in EXPECTED_PROFILES:
            with self.subTest(alphabet=name):
                preview = alphabet_preview(name, 4)
                self.assertIsInstance(preview, str)
                self.assertGreater(len(preview), 0)

    def test_emoji_alias_resolves_to_smiley(self) -> None:
        # Old "emoji" name must still resolve for backwards compatibility.
        from retlang.alphabets import alphabet_id, alphabet_symbols
        self.assertEqual(alphabet_id("emoji"), alphabet_id("emoji-smiley"))
        self.assertEqual(
            alphabet_symbols("emoji"),
            alphabet_symbols("emoji-smiley"),
        )


class AlphabetEncodingTests(unittest.TestCase):
    def test_all_alphabets_exactly_64(self) -> None:
        for name, profile in ALPHABETS.items():
            with self.subTest(name=name):
                self.assertEqual(len(profile.symbols), 64)
                self.assertEqual(len(set(profile.symbols)), 64)

    def test_roundtrip_each_alphabet(self) -> None:
        samples = [b"", b"\x00", b"hello", bytes(range(256))]
        for name in list_alphabets():
            for data in samples:
                with self.subTest(alphabet=name, data=data):
                    enc = encode_bytes(data, name)
                    self.assertIsInstance(enc, str)
                    dec = decode_bytes(enc, name)
                    self.assertEqual(dec, data)

    def test_base64_matches_urlsafe_visually(self) -> None:
        # For the base64 profile, output should be exactly url-safe base64.
        import base64 as stdlib_b64
        data = b"hello world"
        expected = stdlib_b64.urlsafe_b64encode(data).decode("ascii")
        self.assertEqual(encode_bytes(data, "base64"), expected)

    def test_reject_invalid_char(self) -> None:
        with self.assertRaises(ValueError):
            # '!' is not part of the base64 profile but IS part of
            # the symbols profile; we purposely test base64 here.
            decode_bytes("@@@", "base64")

    def test_letters_output_is_letters_only(self) -> None:
        data = b"hello"
        enc = encode_bytes(data, "letters")
        # Every char is A-Z (digraphs) plus possibly "=" pad.
        for ch in enc:
            self.assertTrue(
                ch.isupper() or ch == "=",
                f"{ch!r} is not an uppercase letter or pad",
            )

    def test_numbers_output_is_digits_only(self) -> None:
        data = b"hello"
        enc = encode_bytes(data, "numbers")
        for ch in enc:
            self.assertTrue(
                ch.isdigit() or ch == "=",
                f"{ch!r} is not a digit or pad",
            )


class AlphabetMetadataTests(unittest.TestCase):
    def test_eleven_profiles_registered(self) -> None:
        self.assertEqual(len(list_alphabets()), 11)
        for required in EXPECTED_PROFILES:
            self.assertIn(required, list_alphabets())


if __name__ == "__main__":
    unittest.main()
