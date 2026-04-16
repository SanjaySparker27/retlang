"""Tests for retlang.ui: HTTP server."""

from __future__ import annotations

import http.client
import json
import threading
import time
import unittest

from retlang.ui import build_server


class UIServerFixture:
    def __init__(self) -> None:
        self.server, self.port = build_server(0)
        # build_server tries ports sequentially from the given one; port=0
        # tells _pick_port to start the walk at 0 (still finds free port).
        self.thread = threading.Thread(
            target=self.server.serve_forever, daemon=True
        )

    def start(self) -> None:
        self.thread.start()
        # Tiny wait so the thread is ready to accept.
        for _ in range(50):
            try:
                conn = http.client.HTTPConnection(
                    "127.0.0.1", self.port, timeout=1
                )
                conn.request("GET", "/healthz")
                resp = conn.getresponse()
                resp.read()
                if resp.status == 200:
                    return
            except Exception:
                time.sleep(0.01)
        raise RuntimeError("server did not come up")

    def stop(self) -> None:
        self.server.shutdown()
        self.thread.join(timeout=2)
        self.server.server_close()

    def post_json(self, path: str, payload: dict) -> tuple[int, dict]:
        body = json.dumps(payload).encode("utf-8")
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request(
            "POST",
            path,
            body=body,
            headers={"Content-Type": "application/json"},
        )
        resp = conn.getresponse()
        raw = resp.read().decode("utf-8")
        data = json.loads(raw) if raw else {}
        return resp.status, data


class TestUIAPIs(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fx = UIServerFixture()
        cls.fx.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.fx.stop()

    def test_alphabets(self) -> None:
        status, data = self.fx.post_json("/api/alphabets", {})
        self.assertEqual(status, 200)
        self.assertIn("alphabets", data)
        names = [a["name"] for a in data["alphabets"]]
        self.assertIn("base64", names)

    def test_suggest_phrase(self) -> None:
        status, data = self.fx.post_json(
            "/api/suggest-phrase", {"words": 4}
        )
        self.assertEqual(status, 200)
        self.assertIn("phrase", data)
        self.assertEqual(len(data["phrase"].split("-")), 4)
        self.assertGreater(data["bits"], 0)

    def test_encrypt_decrypt_roundtrip(self) -> None:
        status, data = self.fx.post_json(
            "/api/encrypt",
            {
                "plaintext": "hello",
                "passphrase": "pw",
                "alphabet": "base64",
                "strength": "fast",
            },
        )
        self.assertEqual(status, 200)
        ct = data["ciphertext"]
        status, data = self.fx.post_json(
            "/api/decrypt",
            {
                "ciphertext": ct,
                "passphrase": "pw",
                "alphabet": "base64",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["plaintext"], "hello")

    def test_share_open_roundtrip(self) -> None:
        status, data = self.fx.post_json(
            "/api/share",
            {
                "plaintext": "secret",
                "passphrase": "pw",
                "strength": "fast",
            },
        )
        self.assertEqual(status, 200)
        url = data["url"]
        self.assertTrue(url.startswith("retlang://v1/"))
        status, data = self.fx.post_json(
            "/api/open", {"url": url, "passphrase": "pw"}
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["plaintext"], "secret")

    def test_strength(self) -> None:
        status, data = self.fx.post_json(
            "/api/strength", {"passphrase": "correct-horse-battery-staple"}
        )
        self.assertEqual(status, 200)
        self.assertIn("bits", data)
        self.assertIn("verdict", data)

    def test_unknown_endpoint(self) -> None:
        status, data = self.fx.post_json("/api/nope", {})
        self.assertEqual(status, 404)
        self.assertIn("error", data)

    def test_missing_content_type(self) -> None:
        conn = http.client.HTTPConnection("127.0.0.1", self.fx.port, timeout=5)
        conn.request("POST", "/api/alphabets", body=b"{}")
        resp = conn.getresponse()
        self.assertEqual(resp.status, 415)


if __name__ == "__main__":
    unittest.main()
