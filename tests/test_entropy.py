"""Tests for retlang.entropy: passphrase strength scorer."""

from __future__ import annotations

import os
import sys
import unittest

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from retlang.entropy import format_report, score  # noqa: E402


class TestEntropyScore(unittest.TestCase):
    def test_empty_passphrase(self) -> None:
        result = score("")
        self.assertEqual(result["bits"], 0.0)
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["verdict"], "weak")

    def test_single_char(self) -> None:
        result = score("a")
        self.assertEqual(result["verdict"], "weak")
        self.assertLess(result["bits"], 10)

    def test_common_password_low_score(self) -> None:
        result = score("password")
        self.assertEqual(result["verdict"], "weak")
        self.assertLess(result["bits"], 20)
        self.assertTrue(
            any("blacklist" in n for n in result["notes"])
        )

    def test_short_repeated_low_score(self) -> None:
        result = score("aaaaaaaa")
        self.assertIn(result["verdict"], ("weak", "ok"))

    def test_diceware_scores_high(self) -> None:
        result = score("correct-horse-battery-staple-limit-forth")
        self.assertIn(result["verdict"], ("good", "strong", "excellent"))
        self.assertGreater(result["bits"], 60)
        # No obvious blacklist hit.
        self.assertFalse(any("blacklist" in n for n in result["notes"]))

    def test_random_strong_passphrase(self) -> None:
        result = score("G#8k!pQv2^nM7wZ@x4RtY")
        self.assertIn(result["verdict"], ("strong", "excellent"))

    def test_return_shape(self) -> None:
        result = score("abcdef")
        self.assertIn("bits", result)
        self.assertIn("score", result)
        self.assertIn("verdict", result)
        self.assertIn("notes", result)
        self.assertIsInstance(result["bits"], float)
        self.assertIsInstance(result["score"], int)
        self.assertIsInstance(result["verdict"], str)
        self.assertIsInstance(result["notes"], list)

    def test_wrong_type_raises(self) -> None:
        with self.assertRaises(TypeError):
            score(12345)  # type: ignore[arg-type]

    def test_format_report_has_expected_lines(self) -> None:
        report = format_report("correct-horse-battery-staple")
        self.assertIn("retlang passphrase strength report", report)
        self.assertIn("bits", report)
        self.assertIn("verdict", report)
        self.assertIn("notes", report)


if __name__ == "__main__":
    unittest.main()
