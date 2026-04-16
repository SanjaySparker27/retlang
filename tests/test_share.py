"""Tests for retlang.share: retlang:// URL format and round-trip."""

from __future__ import annotations

import unittest

from retlang.share import (
    RETLANG_URL_PREFIX,
    is_retlang_url,
    make_url,
    open_url,
    parse_url,
    share,
)


class TestMakeParseURL(unittest.TestCase):
    def test_make_url_prefix(self) -> None:
        url = make_url(b"hello world")
        self.assertTrue(url.startswith(RETLANG_URL_PREFIX))
        self.assertTrue(url.startswith("retlang://v1/"))

    def test_parse_url_roundtrip(self) -> None:
        payload = b"\x00\x01\x02\x03some-binary\xFF\xFE"
        url = make_url(payload)
        back = parse_url(url)
        self.assertEqual(back, payload)

    def test_parse_url_with_whitespace(self) -> None:
        url = make_url(b"abcdef")
        back = parse_url("   " + url + "\n")
        self.assertEqual(back, b"abcdef")

    def test_empty_envelope_rejected(self) -> None:
        with self.assertRaises(ValueError):
            make_url(b"")

    def test_malformed_url_rejected_missing_prefix(self) -> None:
        with self.assertRaises(ValueError):
            parse_url("hello world")

    def test_malformed_url_rejected_bad_chars(self) -> None:
        with self.assertRaises(ValueError):
            parse_url("retlang://v1/!!not-valid!!")

    def test_malformed_url_rejected_empty_body(self) -> None:
        with self.assertRaises(ValueError):
            parse_url("retlang://v1/")

    def test_wrong_type_raises(self) -> None:
        with self.assertRaises(TypeError):
            make_url("not bytes")  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            parse_url(b"bytes not str")  # type: ignore[arg-type]


class TestIsRetlangURL(unittest.TestCase):
    def test_positive(self) -> None:
        url = make_url(b"abc")
        self.assertTrue(is_retlang_url(url))

    def test_negative(self) -> None:
        self.assertFalse(is_retlang_url("https://example.com"))
        self.assertFalse(is_retlang_url("retlang://v2/abc"))
        self.assertFalse(is_retlang_url(""))
        self.assertFalse(is_retlang_url("retlang://v1/"))
        # Non-strings do not crash.
        self.assertFalse(is_retlang_url(12345))  # type: ignore[arg-type]


class TestShareOpen(unittest.TestCase):
    def test_share_open_roundtrip(self) -> None:
        url = share("top secret", "pw", strength="fast")
        self.assertTrue(url.startswith("retlang://v1/"))
        self.assertEqual(open_url(url, "pw"), "top secret")

    def test_wrong_passphrase_fails(self) -> None:
        url = share("hello", "right", strength="fast")
        with self.assertRaises(Exception):
            open_url(url, "wrong")

    def test_share_unicode(self) -> None:
        msg = "naïve — 你好 🌐"
        url = share(msg, "pass", strength="fast")
        self.assertEqual(open_url(url, "pass"), msg)

    def test_share_with_wordmap(self) -> None:
        wm = {"alpha": "ZZZ", "beta": "YYY"}
        url = share("alpha and beta", "pw", wordmap=wm, strength="fast")
        self.assertEqual(open_url(url, "pw", wordmap=wm), "alpha and beta")


if __name__ == "__main__":
    unittest.main()
