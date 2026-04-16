"""QR code rendering -- optional dependency.

QR encoding (Reed-Solomon, mask scoring, version selection) is out of
scope for a pure-stdlib implementation. The `qrcode` PyPI package is
gated behind a `try/except ImportError` and exposed via the `retlang[qr]`
extra.

Public API
----------
- qr_available() -> bool
- qr_ascii(text)  -> str   (ASCII art; RuntimeError if qrcode missing)
- qr_png(text, path) -> None (writes PNG; RuntimeError if qrcode missing)
"""

from __future__ import annotations

from typing import Optional

_INSTALL_MSG = (
    "QR support is an optional feature. "
    "Install `pip install retlang[qr]` to enable QR output."
)


def _try_import():
    try:
        import qrcode  # type: ignore
        return qrcode
    except ImportError:
        return None


def qr_available() -> bool:
    """Return True if the optional `qrcode` dependency is importable."""
    return _try_import() is not None


def qr_ascii(text: str) -> str:
    """Return an ASCII-art QR code encoding `text`.

    Raises RuntimeError if `qrcode` is not installed.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a str")
    qrcode = _try_import()
    if qrcode is None:
        raise RuntimeError(_INSTALL_MSG)
    qr = qrcode.QRCode(border=1)
    qr.add_data(text)
    qr.make(fit=True)

    # Render with printable block characters. `qr.get_matrix()` yields a
    # list[list[bool]] where True = dark module.
    matrix = qr.get_matrix()
    dark = "\u2588\u2588"  # two full blocks, preserves aspect ratio
    light = "  "
    lines = []
    for row in matrix:
        lines.append("".join(dark if cell else light for cell in row))
    return "\n".join(lines) + "\n"


def qr_png(text: str, path: str, box_size: Optional[int] = 10) -> None:
    """Write a PNG QR code of `text` to `path`.

    Raises RuntimeError if `qrcode` is not installed.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a str")
    if not isinstance(path, str):
        raise TypeError("path must be a str")
    qrcode = _try_import()
    if qrcode is None:
        raise RuntimeError(_INSTALL_MSG)
    qr = qrcode.QRCode(border=2, box_size=box_size or 10)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(path)


__all__ = ["qr_available", "qr_ascii", "qr_png"]
