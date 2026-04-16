"""Tests for retlang.phrase: diceware suggestion and entropy math."""

from __future__ import annotations

import math
import unittest
from unittest import mock

from retlang.phrase import (
    phrase_entropy_bits,
    suggest_phrase,
    wordlist_size,
)


class TestWordlist(unittest.TestCase):
    def test_wordlist_has_enough_words(self) -> None:
        size = wordlist_size()
        self.assertGreaterEqual(size, 4096)

    def test_suggest_phrase_default(self) -> None:
        phrase = suggest_phrase()
        parts = phrase.split("-")
        self.assertEqual(len(parts), 6)
        for word in parts:
            self.assertTrue(word.isalpha())
            self.assertTrue(word.islower() or word.isalpha())

    def test_suggest_phrase_custom_count(self) -> None:
        phrase = suggest_phrase(words=4)
        self.assertEqual(len(phrase.split("-")), 4)

    def test_suggest_phrase_custom_separator(self) -> None:
        phrase = suggest_phrase(words=3, separator=".")
        self.assertEqual(len(phrase.split(".")), 3)

    def test_all_words_come_from_wordlist(self) -> None:
        # Load wordlist directly and check the suggestion subset matches.
        from retlang.phrase import _load_wordlist
        pool = set(_load_wordlist())
        phrase = suggest_phrase(words=10)
        for word in phrase.split("-"):
            self.assertIn(word, pool)

    def test_invalid_word_count(self) -> None:
        with self.assertRaises(ValueError):
            suggest_phrase(words=0)
        with self.assertRaises(TypeError):
            suggest_phrase(words="six")  # type: ignore[arg-type]


class TestSecretsUsage(unittest.TestCase):
    def test_uses_secrets_choice(self) -> None:
        """suggest_phrase must call secrets.choice, not random.choice."""
        with mock.patch("retlang.phrase.secrets") as mock_secrets:
            # secrets.choice returns a constant for the test.
            mock_secrets.choice.return_value = "testword"
            # secrets.SystemRandom is accessed at import-time; do not
            # blow up if a later test calls _RNG.
            mock_secrets.SystemRandom.return_value = mock.MagicMock()
            phrase = suggest_phrase(words=3)
        self.assertEqual(mock_secrets.choice.call_count, 3)
        self.assertEqual(phrase, "testword-testword-testword")


class TestEntropyMath(unittest.TestCase):
    def test_known_value(self) -> None:
        # 6 words from a 7776-word list = ~77.55 bits.
        bits = phrase_entropy_bits(6, 7776)
        self.assertAlmostEqual(bits, 6 * math.log2(7776), places=6)

    def test_monotonic_increase(self) -> None:
        b4 = phrase_entropy_bits(4, 7776)
        b6 = phrase_entropy_bits(6, 7776)
        self.assertLess(b4, b6)

    def test_invalid_inputs(self) -> None:
        with self.assertRaises(ValueError):
            phrase_entropy_bits(0, 7776)
        with self.assertRaises(ValueError):
            phrase_entropy_bits(6, 1)
        with self.assertRaises(TypeError):
            phrase_entropy_bits("six", 7776)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
