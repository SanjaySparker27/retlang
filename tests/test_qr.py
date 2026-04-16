"""Tests for retlang.qr: optional QR code support."""

from __future__ import annotations

import unittest

from retlang.qr import qr_ascii, qr_available, qr_png


class TestQRCode(unittest.TestCase):
    def test_qr_available_returns_bool(self) -> None:
        result = qr_available()
        self.assertIsInstance(result, bool)

    def test_qr_ascii_behavior(self) -> None:
        """qr_ascii either succeeds (qrcode installed) or raises RuntimeError."""
        if qr_available():
            out = qr_ascii("retlang://v1/abc")
            self.assertIsInstance(out, str)
            self.assertGreater(len(out), 0)
        else:
            with self.assertRaises(RuntimeError) as ctx:
                qr_ascii("retlang://v1/abc")
            msg = str(ctx.exception)
            self.assertIn("retlang[qr]", msg)

    def test_qr_png_behavior(self) -> None:
        """qr_png raises RuntimeError when qrcode is not installed."""
        if not qr_available():
            with self.assertRaises(RuntimeError) as ctx:
                qr_png("retlang://v1/abc", "/tmp/retlang-test-qr.png")
            self.assertIn("retlang[qr]", str(ctx.exception))

    def test_type_checks(self) -> None:
        with self.assertRaises(TypeError):
            qr_ascii(123)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            qr_png(123, "/tmp/x.png")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
