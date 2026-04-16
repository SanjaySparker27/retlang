"""Wordmap substitution demo.

Uses examples/sample-wordmap.json to translate a few sensitive nouns
before the cipher runs. The same mapping is required to decrypt.

Run:  python examples/wordmap_example.py
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from retlang import decrypt, encrypt


def main() -> None:
    passphrase = "sample-phrase"
    mapping_path = os.path.join(HERE, "sample-wordmap.json")
    with open(mapping_path, "r", encoding="utf-8") as fh:
        wordmap = json.load(fh)

    plaintext = "Attack the castle at dawn. The key is under the rock."
    print("plaintext :", plaintext)

    ciphertext = encrypt(plaintext, passphrase, alphabet="runes", wordmap=wordmap)
    print("ciphertext:", ciphertext)

    recovered = decrypt(ciphertext, passphrase, alphabet="runes", wordmap=wordmap)
    print("decrypted :", recovered)


if __name__ == "__main__":
    main()
