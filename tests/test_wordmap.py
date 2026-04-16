"""Tests for the optional wordmap substitution layer."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from retlang import decrypt, encrypt  # noqa: E402
from retlang.layers.wordmap import apply_wordmap, reverse_wordmap  # noqa: E402


PASSPHRASE = "wordmap-tests"


class WordmapLayerTests(unittest.TestCase):
    def test_whole_word_substitution(self) -> None:
        mapping = {"attack": "picnic", "dawn": "sunrise"}
        text = "Attack at dawn!"
        result = apply_wordmap(text, mapping)
        self.assertEqual(result, "picnic at sunrise!")

    def test_preserves_whitespace_and_punct(self) -> None:
        mapping = {"hello": "hi"}
        text = "  hello,  world!\nhello\t."
        result = apply_wordmap(text, mapping)
        self.assertEqual(result, "  hi,  world!\nhi\t.")

    def test_case_insensitive_matching(self) -> None:
        mapping = {"gold": "apple"}
        text = "Gold GOLD gold GoLd"
        result = apply_wordmap(text, mapping)
        self.assertEqual(result, "apple apple apple apple")

    def test_does_not_split_partial_words(self) -> None:
        mapping = {"cat": "dog"}
        text = "caterpillar concatenate cat"
        # "cat" should ONLY match the standalone word, not substrings.
        result = apply_wordmap(text, mapping)
        self.assertEqual(result, "caterpillar concatenate dog")

    def test_reverse_roundtrip(self) -> None:
        mapping = {"attack": "picnic", "dawn": "sunrise", "base": "meadow"}
        text = "attack at dawn at base"
        forward = apply_wordmap(text, mapping)
        back = reverse_wordmap(forward, mapping)
        # Because case collapses to lowercase in round-trip, we compare
        # case-insensitively here.
        self.assertEqual(back.lower(), text.lower())

    def test_none_mapping_noop(self) -> None:
        self.assertEqual(apply_wordmap("hello", None), "hello")
        self.assertEqual(reverse_wordmap("hello", None), "hello")

    def test_non_bijective_reject(self) -> None:
        mapping = {"a": "x", "b": "x"}  # both map to "x" -> not invertible
        with self.assertRaises(ValueError):
            reverse_wordmap("x x", mapping)


class WordmapIntegrationTests(unittest.TestCase):
    def test_encrypt_decrypt_with_wordmap(self) -> None:
        mapping = {"attack": "picnic", "dawn": "sunrise"}
        plaintext = "attack at dawn"
        ct = encrypt(plaintext, PASSPHRASE, wordmap=mapping)
        recovered = decrypt(ct, PASSPHRASE, wordmap=mapping)
        self.assertEqual(recovered.lower(), plaintext.lower())

    def test_wordmap_changes_ciphertext(self) -> None:
        plaintext = "attack at dawn"
        ct_plain = encrypt(plaintext, PASSPHRASE)
        ct_mapped = encrypt(plaintext, PASSPHRASE, wordmap={"attack": "picnic"})
        # They should be distinct (different inputs to the cipher stream).
        self.assertNotEqual(ct_plain, ct_mapped)


if __name__ == "__main__":
    unittest.main()
