"""Tests for retlang.agent: clipboard watcher."""

from __future__ import annotations

import os
import sys
import unittest

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from retlang.agent import _extract_url, watch  # noqa: E402
from retlang.share import share  # noqa: E402


class TestExtractURL(unittest.TestCase):
    def test_plain_url(self) -> None:
        url = share("hi", "pw", strength="fast")
        self.assertEqual(_extract_url(url), url)

    def test_url_in_sentence(self) -> None:
        url = share("hi", "pw", strength="fast")
        text = f"check this out: {url} -- thanks!"
        self.assertEqual(_extract_url(text), url)

    def test_no_url(self) -> None:
        self.assertIsNone(_extract_url("hello world"))
        self.assertIsNone(_extract_url(""))


class TestWatch(unittest.TestCase):
    def test_callback_invoked_once(self) -> None:
        url = share("hi", "pw", strength="fast")
        seen = []

        clip = iter([url, url, url, url])

        def reader():
            try:
                return next(clip)
            except StopIteration:
                return None

        def on_detect(u: str) -> None:
            seen.append(u)

        watch(
            on_detect,
            interval=0.0001,
            once=True,
            clipboard_reader=reader,
            max_iterations=5,
        )
        self.assertEqual(seen, [url])

    def test_dedup_same_url(self) -> None:
        """Same URL reported repeatedly must fire exactly once."""
        url = share("hello", "pw", strength="fast")
        calls = []

        def reader():
            return url

        def on_detect(u: str) -> None:
            calls.append(u)

        watch(
            on_detect,
            interval=0.0001,
            clipboard_reader=reader,
            max_iterations=10,
        )
        self.assertEqual(len(calls), 1)

    def test_different_urls_fire_twice(self) -> None:
        a = share("first", "pw", strength="fast")
        b = share("second", "pw", strength="fast")
        seq = iter([a, a, a, b, b, b, a, a])

        def reader():
            try:
                return next(seq)
            except StopIteration:
                return None

        calls = []

        def on_detect(u: str) -> None:
            calls.append(u)

        watch(
            on_detect,
            interval=0.0001,
            clipboard_reader=reader,
            max_iterations=10,
        )
        # a, then b, then a again (after b).
        self.assertEqual(len(calls), 3)
        self.assertEqual(calls[0], a)
        self.assertEqual(calls[1], b)
        self.assertEqual(calls[2], a)

    def test_no_url_never_fires(self) -> None:
        def reader():
            return "just some boring text"

        calls = []
        watch(
            calls.append,
            interval=0.0001,
            clipboard_reader=reader,
            max_iterations=5,
        )
        self.assertEqual(calls, [])

    def test_invalid_interval(self) -> None:
        with self.assertRaises(ValueError):
            watch(lambda _u: None, interval=0, max_iterations=1)


if __name__ == "__main__":
    unittest.main()
