"""Local HTTP server that exposes retlang as a browser UI.

Binds to 127.0.0.1 only (never 0.0.0.0). Auto-picks the next free port
if the requested one is busy. Serves static files from
`src/retlang/static/` (written by a sibling agent) and JSON APIs under
`/api/*` that mirror the Python library.

Endpoints
---------
GET  /                     static/index.html
GET  /static/<file>        static asset
POST /api/encrypt          {plaintext, passphrase, alphabet, strength, wordmap?}
POST /api/decrypt          {ciphertext, passphrase, alphabet, wordmap?}
POST /api/share            {plaintext, passphrase, wordmap?, strength?}
POST /api/open             {url, passphrase, wordmap?}
POST /api/suggest-phrase   {words?: int, separator?: str}
POST /api/strength         {passphrase: str}
POST /api/alphabets        -> {alphabets:[{name,id,preview}, ...]}
"""

from __future__ import annotations

import http.server
import json
import mimetypes
import signal
import socket
import sys
import threading
import webbrowser
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple
from urllib.parse import urlparse

from .alphabets import NAME_TO_ID, alphabet_preview, list_alphabets
from .cipher import decrypt as _decrypt, encrypt as _encrypt
from .entropy import score as _score
from .phrase import phrase_entropy_bits, suggest_phrase, wordlist_size
from .share import open_url as _open_url, share as _share


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _static_dir() -> Path:
    return Path(__file__).parent / "static"


def _resolve_static_path(rel: str) -> Optional[Path]:
    """Resolve a /static/<rel> request to a safe filesystem path.

    Returns None if the request escapes the static directory.
    """
    base = _static_dir().resolve()
    candidate = (base / rel).resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        return None
    if not candidate.is_file():
        return None
    return candidate


def _pick_port(preferred: int, attempts: int = 10) -> int:
    """Return a free port starting at `preferred` and walking upward.

    If preferred <= 0, let the OS pick any free ephemeral port.
    """
    if preferred <= 0:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return sock.getsockname()[1]
    for offset in range(attempts):
        port = preferred + offset
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError(
        f"could not find a free port in {preferred}..{preferred + attempts - 1}"
    )


# ------------------------------------------------------------------
# API handlers
# ------------------------------------------------------------------

def _api_encrypt(body: Dict[str, Any]) -> Dict[str, Any]:
    ciphertext = _encrypt(
        body["plaintext"],
        body["passphrase"],
        alphabet=body.get("alphabet", "base64"),
        wordmap=body.get("wordmap"),
        strength=body.get("strength"),
    )
    return {"ciphertext": ciphertext}


def _api_decrypt(body: Dict[str, Any]) -> Dict[str, Any]:
    plaintext = _decrypt(
        body["ciphertext"],
        body["passphrase"],
        alphabet=body.get("alphabet", "base64"),
        wordmap=body.get("wordmap"),
    )
    return {"plaintext": plaintext}


def _api_share(body: Dict[str, Any]) -> Dict[str, Any]:
    url = _share(
        body["plaintext"],
        body["passphrase"],
        wordmap=body.get("wordmap"),
        strength=body.get("strength", "normal"),
    )
    return {"url": url}


def _api_open(body: Dict[str, Any]) -> Dict[str, Any]:
    plaintext = _open_url(
        body["url"],
        body["passphrase"],
        wordmap=body.get("wordmap"),
    )
    return {"plaintext": plaintext}


def _api_suggest_phrase(body: Dict[str, Any]) -> Dict[str, Any]:
    words = int(body.get("words", 6))
    separator = body.get("separator", "-")
    phrase = suggest_phrase(words=words, separator=separator)
    return {
        "phrase": phrase,
        "bits": phrase_entropy_bits(words, wordlist_size()),
        "words": words,
    }


def _api_strength(body: Dict[str, Any]) -> Dict[str, Any]:
    result = _score(body["passphrase"])
    return result


def _api_alphabets(body: Dict[str, Any]) -> Dict[str, Any]:
    out = []
    for name in list_alphabets():
        out.append(
            {
                "name": name,
                "id": NAME_TO_ID[name],
                "preview": alphabet_preview(name, 16),
            }
        )
    return {"alphabets": out}


_API_ROUTES: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
    "/api/encrypt":        _api_encrypt,
    "/api/decrypt":        _api_decrypt,
    "/api/share":          _api_share,
    "/api/open":           _api_open,
    "/api/suggest-phrase": _api_suggest_phrase,
    "/api/strength":       _api_strength,
    "/api/alphabets":      _api_alphabets,
}


# ------------------------------------------------------------------
# Handler
# ------------------------------------------------------------------

class RetlangHandler(http.server.BaseHTTPRequestHandler):
    server_version = "retlang-ui/1"

    # ---- logging ----
    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write(
            "[retlang-ui] %s - %s\n" % (self.address_string(), fmt % args)
        )

    # ---- cors / origin check ----
    def _origin_allowed(self) -> bool:
        origin = self.headers.get("Origin")
        if origin is None:
            return True
        host = self.headers.get("Host", "")
        # Accept http://127.0.0.1:<same-host> or http://localhost:<same-host>.
        for prefix in ("http://127.0.0.1", "http://localhost"):
            if origin.startswith(prefix):
                # Allow either exact host:port match or any port under prefix.
                if host and origin.endswith(host):
                    return True
                if ":" not in origin[len(prefix):]:
                    return True
                return True
        return False

    def _send_json(self, status: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path, status: int = 200) -> None:
        data = path.read_bytes()
        mime, _ = mimetypes.guess_type(str(path))
        if mime is None:
            mime = "application/octet-stream"
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _send_error_text(self, status: int, message: str) -> None:
        self._send_json(status, {"error": message})

    # ---- GET ----
    def do_GET(self) -> None:  # noqa: N802 - stdlib naming
        if not self._origin_allowed():
            self._send_error_text(403, "origin not allowed")
            return
        url = urlparse(self.path)
        path = url.path
        if path in ("/", "/index.html"):
            index = _static_dir() / "index.html"
            if index.is_file():
                self._send_file(index)
                return
            # Fallback: emit a tiny bootstrap page so the UI is usable even
            # if the frontend agent has not written index.html yet.
            self._send_file_text(
                "<!doctype html><title>retlang</title>"
                "<h1>retlang UI</h1>"
                "<p>Static assets are not yet available. "
                "The API is running at /api/*.</p>"
            )
            return
        if path.startswith("/static/"):
            rel = path[len("/static/"):]
            resolved = _resolve_static_path(rel)
            if resolved is None:
                self._send_error_text(404, "not found")
                return
            self._send_file(resolved)
            return
        if path == "/healthz":
            self._send_json(200, {"ok": True})
            return
        self._send_error_text(404, "not found")

    def _send_file_text(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ---- POST ----
    def do_POST(self) -> None:  # noqa: N802 - stdlib naming
        if not self._origin_allowed():
            self._send_error_text(403, "origin not allowed")
            return
        url = urlparse(self.path)
        path = url.path
        handler = _API_ROUTES.get(path)
        if handler is None:
            self._send_error_text(404, "unknown endpoint")
            return

        ctype = self.headers.get("Content-Type", "")
        if "application/json" not in ctype.lower():
            self._send_error_text(
                415, "Content-Type must be application/json"
            )
            return

        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            body: Dict[str, Any] = {}
        else:
            raw = self.rfile.read(length)
            try:
                body = json.loads(raw.decode("utf-8"))
            except Exception as exc:
                self._send_error_text(400, f"invalid JSON body: {exc}")
                return
            if not isinstance(body, dict):
                self._send_error_text(400, "JSON body must be an object")
                return

        try:
            result = handler(body)
        except KeyError as exc:
            self._send_error_text(400, f"missing field: {exc.args[0]}")
            return
        except (TypeError, ValueError) as exc:
            self._send_error_text(400, str(exc))
            return
        except Exception as exc:  # noqa: BLE001 - surface any crypto failure
            self._send_error_text(500, f"{type(exc).__name__}: {exc}")
            return

        self._send_json(200, result)


# ------------------------------------------------------------------
# Server control
# ------------------------------------------------------------------

def build_server(port: int) -> Tuple[http.server.HTTPServer, int]:
    """Return (server, actual_port). Binds to 127.0.0.1 only."""
    actual = _pick_port(port)
    server = http.server.HTTPServer(("127.0.0.1", actual), RetlangHandler)
    return server, actual


def launch(port: int = 8787, open_browser: bool = True) -> None:
    """Start the UI server and block until SIGINT."""
    server, actual = build_server(port)
    url = f"http://127.0.0.1:{actual}"
    sys.stderr.write(f"retlang UI listening on {url}\n")

    def _shutdown(*_args: Any) -> None:
        sys.stderr.write("\nretlang UI shutting down...\n")
        threading.Thread(target=server.shutdown, daemon=True).start()

    # signal.signal() only works in the main thread. Skip silently in worker threads
    # (e.g., when launched from tests or embedded in another app).
    if threading.current_thread() is threading.main_thread():
        try:
            signal.signal(signal.SIGINT, _shutdown)
        except (AttributeError, ValueError):
            pass
        try:
            signal.signal(signal.SIGTERM, _shutdown)
        except (AttributeError, ValueError):
            pass

    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        server.serve_forever()
    finally:
        server.server_close()


__all__ = ["RetlangHandler", "launch", "build_server"]
