"""Clipboard-watcher agent.

Polls the system clipboard on a light interval. When a retlang:// URL
appears (and differs from the previous one seen), it invokes the user's
callback. `agent_cli()` provides a ready-made interactive loop that
prompts for a passphrase and prints the decrypted plaintext.

Clipboard backends (auto-detected in order):
    - macOS     : `pbpaste`
    - Linux     : `xclip -selection clipboard -o`
    - Wayland   : `wl-paste`
    - Windows   : PowerShell `Get-Clipboard`

Always subprocess-based; no third-party packages.
"""

from __future__ import annotations

import getpass
import shutil
import subprocess
import sys
import time
from typing import Callable, List, Optional, Tuple

from .share import is_retlang_url, open_url


# ------------------------------------------------------------------
# Clipboard detection
# ------------------------------------------------------------------

def _candidate_backends() -> List[Tuple[str, List[str]]]:
    """Return (label, argv) tuples to try in priority order."""
    plat = sys.platform
    candidates: List[Tuple[str, List[str]]] = []
    if plat == "darwin":
        candidates.append(("pbpaste", ["pbpaste"]))
    elif plat.startswith("linux"):
        # Prefer wl-paste on Wayland, fall back to xclip / xsel.
        candidates.append(("wl-paste", ["wl-paste", "--no-newline"]))
        candidates.append(("xclip", ["xclip", "-selection", "clipboard", "-o"]))
        candidates.append(("xsel", ["xsel", "--clipboard", "--output"]))
    elif plat == "win32":
        candidates.append(
            ("Get-Clipboard", ["powershell", "-NoProfile", "-Command", "Get-Clipboard"])
        )
    else:
        # Unknown platform: try macOS/Linux in order.
        candidates.append(("pbpaste", ["pbpaste"]))
        candidates.append(("xclip", ["xclip", "-selection", "clipboard", "-o"]))
    return candidates


def _pick_backend() -> Optional[List[str]]:
    for label, argv in _candidate_backends():
        if shutil.which(argv[0]) is not None:
            return argv
    return None


def read_clipboard() -> Optional[str]:
    """Return the current clipboard text, or None if no backend is available.

    Returns an empty string if the clipboard is empty but the backend worked.
    Returns None if the backend failed (missing binary, non-zero exit, etc.).
    """
    argv = _pick_backend()
    if argv is None:
        return None
    try:
        proc = subprocess.run(
            argv,
            check=False,
            capture_output=True,
            text=True,
            timeout=2.0,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


# ------------------------------------------------------------------
# Watcher
# ------------------------------------------------------------------

def _extract_url(text: str) -> Optional[str]:
    """Return the first retlang:// URL-looking token in `text`, or None."""
    if not text:
        return None
    for token in text.split():
        if is_retlang_url(token):
            return token.strip()
    stripped = text.strip()
    if is_retlang_url(stripped):
        return stripped
    return None


def watch(
    on_detect: Callable[[str], None],
    *,
    interval: float = 0.5,
    once: bool = False,
    max_iterations: Optional[int] = None,
    clipboard_reader: Callable[[], Optional[str]] = read_clipboard,
) -> None:
    """Poll the clipboard and invoke `on_detect(url)` when a new URL appears.

    Deduplicates: the same URL will not re-trigger until a different URL
    (or different clipboard content) appears in between.

    Parameters
    ----------
    on_detect : callback invoked with the detected retlang URL string.
    interval  : polling interval in seconds.
    once      : if True, return after the first detection.
    max_iterations : if set, stop after this many polls (mostly for tests).
    clipboard_reader : override for tests; default is `read_clipboard`.
    """
    if interval <= 0:
        raise ValueError("interval must be > 0")
    last_seen: Optional[str] = None
    iterations = 0
    while True:
        if max_iterations is not None and iterations >= max_iterations:
            return
        iterations += 1

        text = clipboard_reader()
        url = _extract_url(text) if text is not None else None
        if url is not None and url != last_seen:
            last_seen = url
            on_detect(url)
            if once:
                return
        # If the clipboard changed away from the URL, reset dedup so a
        # re-copy of the same URL does fire again.
        if url is None and last_seen is not None:
            last_seen = None

        try:
            time.sleep(interval)
        except KeyboardInterrupt:
            return


# ------------------------------------------------------------------
# Interactive CLI entrypoint
# ------------------------------------------------------------------

def agent_cli(prompt_before_decrypt: bool = True) -> None:
    """Interactive clipboard watcher. Ctrl+C to exit."""
    if _pick_backend() is None:
        sys.stderr.write(
            "No clipboard backend available. Install `pbpaste` (macOS), "
            "`xclip`/`xsel` (Linux X11), or `wl-paste` (Wayland).\n"
        )
        raise SystemExit(2)

    sys.stderr.write(
        "retlang agent: watching clipboard for retlang:// URLs. Ctrl+C to stop.\n"
    )

    def _handle(url: str) -> None:
        sys.stderr.write("\nDetected retlang:// URL in clipboard.\n")
        if prompt_before_decrypt:
            try:
                choice = input("Decrypt? [Y/n]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                sys.stderr.write("\naborted\n")
                return
            if choice not in ("", "y", "yes"):
                sys.stderr.write("skipped\n")
                return
        try:
            passphrase = getpass.getpass("Passphrase: ")
        except (EOFError, KeyboardInterrupt):
            sys.stderr.write("\naborted\n")
            return
        try:
            plaintext = open_url(url, passphrase)
        except Exception as exc:
            sys.stderr.write(f"decryption failed: {exc}\n")
            return
        sys.stdout.write("--- plaintext ---\n")
        sys.stdout.write(plaintext)
        if not plaintext.endswith("\n"):
            sys.stdout.write("\n")
        sys.stdout.write("--- end ---\n")
        sys.stdout.flush()

    try:
        watch(_handle, interval=0.5, once=False)
    except KeyboardInterrupt:
        sys.stderr.write("\nagent stopped\n")


__all__ = ["read_clipboard", "watch", "agent_cli"]
