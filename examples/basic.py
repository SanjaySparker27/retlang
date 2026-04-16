"""Basic encrypt + decrypt demo.

Run:  python examples/basic.py
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from retlang import decrypt, encrypt


def main() -> None:
    passphrase = "correct horse battery staple"
    message = "Meet me at the library at 7pm."

    ciphertext_b64 = encrypt(message, passphrase, alphabet="base64")
    print("-- base64 alphabet --")
    print("ciphertext:", ciphertext_b64)
    print("decrypted :", decrypt(ciphertext_b64, passphrase, alphabet="base64"))

    ciphertext_emoji = encrypt(message, passphrase, alphabet="emoji-smiley")
    print("\n-- emoji-smiley alphabet --")
    print("ciphertext:", ciphertext_emoji)
    print("decrypted :", decrypt(ciphertext_emoji, passphrase, alphabet="emoji-smiley"))


if __name__ == "__main__":
    main()
