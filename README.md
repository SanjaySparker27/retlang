# retlang

Turn ordinary English into a whispered dialect of symbols, emoji, and glyphs.

`retlang` is a Python 3 library and CLI that encrypts plain text into a reversible "secret language" using passphrase-derived keys, a Vigenere-style stream cipher, optional wordmap substitution, a pluggable output alphabet (base64, letters, numbers, symbols, four emoji packs, geometric shapes, runes, astrological signs), and an HMAC tag for integrity. It has zero runtime dependencies beyond the Python standard library.

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-experimental-orange)
![Repo](https://img.shields.io/badge/github-SanjaySparker27%2Fretlang-black)

## What is this

A toy cipher framework for people who want to pass notes in class, annotate diaries, obfuscate offline backups, build escape-room puzzles, or teach a kid how substitution ciphers feel from the inside. It is reversible, deterministic for a given passphrase, and fun to read. It is not a replacement for real cryptography; see the "Security caveats" section below.

## Install

```bash
git clone https://github.com/SanjaySparker27/retlang && cd retlang && pip install -e .
```

The package is declared in `pyproject.toml` and has no third-party dependencies. Python 3.9 or newer is required.

## Quick start

### CLI

```bash
# Encrypt a message to the default base64 alphabet
retlang encrypt -p hunter2 "hello"

# Encrypt with an emoji food alphabet
retlang encrypt -p hunter2 -a emoji-food "hello"

# Decrypt back to English (alphabet is auto-detected from the envelope)
retlang decrypt -p hunter2 "<paste ciphertext here>"

# Bump the KDF strength up for sensitive drafts
retlang encrypt -p hunter2 -a runes -s strong "meet me at midnight"

# List all available output alphabets
retlang list-alphabets

# Generate a fresh random passphrase you can share out-of-band
retlang genkey --length 24
```

### Python library

```python
from retlang import encrypt, decrypt

token = encrypt("meet me at midnight", passphrase="moonlight", alphabet="runes")
print(token)

plain = decrypt(token, passphrase="moonlight")
print(plain)  # "meet me at midnight"
```

See [docs/USAGE.md](docs/USAGE.md) for every subcommand, every keyword argument, and end-to-end examples.

## Alphabets

Every alphabet maps the output byte stream into a different visual system. Pick one with `-a/--alphabet` on the CLI or `alphabet=` in Python. There are 11 built-in profiles:

| ID | Name             | Preview                     | Notes                                                       |
|----|------------------|-----------------------------|-------------------------------------------------------------|
| 0  | `base64`         | `ABCDEFGH`                  | URL-safe base64, compact, default                           |
| 1  | `letters`        | `AABABBAC`                  | A-Z pairs, 2 chars per 6-bit group (output 2x longer)       |
| 2  | `numbers`        | `00010203`                  | `00`-`63` pairs, 2 chars per 6-bit group                    |
| 3  | `symbols`        | `!@#$%^&*`                  | Punctuation only, 1 char per 6-bit group                    |
| 4  | `emoji-smiley`   | `😀😃😄😁😆😅🤣😂`          | Faces; 1 char per group (UTF-8 multi-byte)                  |
| 5  | `emoji-animals`  | `🐶🐱🐭🐹🐰🦊🐻🐼`          | Animals; 1 char per group                                   |
| 6  | `emoji-food`     | `🍕🍔🍣🍜🍱🍙🍎🍇`          | Food; 1 char per group                                      |
| 7  | `emoji-nature`   | `🌲🌳🌻🌼🌸⛅️☀️🌧️`         | Nature and weather; 1 char per group                        |
| 8  | `geometric`      | `■▲●◆□△○◇`                  | Geometric glyphs; 1 char per group                          |
| 9  | `runes`          | `ᚠᚢᚦᚨᚱᚲᚷᚹ`                  | Elder Futhark; 1 char per group                             |
| 10 | `astro`          | `♈♉♊♋♌♍♎♏`                  | Zodiac and planetary glyphs; 1 char per group               |

The old name `emoji` is kept as an alias for `emoji-smiley` so existing scripts keep working.

All alphabets are fully round-trip safe: encrypt in one, decrypt with the same passphrase, and the plaintext comes back byte-for-byte identical.

## Features

- Passphrase-derived keys via PBKDF2-HMAC-SHA256 (stdlib `hashlib`).
- Vigenere-style stream cipher over the raw byte stream.
- Optional user-supplied wordmap that rewrites whole words before encryption.
- Eleven built-in output alphabets; add your own by registering a 64-symbol list.
- Four PBKDF2 strength presets (`fast`, `normal`, `strong`, `paranoid`) plus an advanced `--iterations` override.
- HMAC-SHA256 integrity tag appended to every ciphertext; tamper detection on decrypt.
- Deterministic encryption for a given passphrase and salt, so fixtures and tests are stable.
- Zero third-party dependencies. Python 3.9+ standard library only.
- Small, auditable codebase; see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

### Strength levels

The `-s/--strength` flag on `encrypt` picks a PBKDF2 iteration count. Higher means slower to brute-force and slower to decrypt — the cost is paid on both sides.

| Level      | Iterations | Typical time | When to pick it                                             |
|------------|-----------:|-------------:|-------------------------------------------------------------|
| `fast`     |    100,000 |       ~50 ms | Puzzles, low-sensitivity notes, latency-sensitive scripts.  |
| `normal`   |    200,000 |      ~100 ms | Default. Fine for diaries and everyday "hide from casuals". |
| `strong`   |    500,000 |      ~250 ms | Drafts you'd rather a determined snoop could not brute.     |
| `paranoid` |  1,000,000 |      ~500 ms | Maximum resistance within the toy-crypto threat model.      |

Picking a higher level does **not** change the underlying threat model. Retlang remains toy-grade; stronger iteration counts only raise the cost of offline brute-force guessing against the passphrase. Use `-s paranoid` when you want that cost raised and are willing to wait half a second on decrypt.

Advanced users can override the preset with `--iterations INT` for a custom count (mutually exclusive with `-s/--strength`).

## How it works

1. **Key derivation.** Your passphrase plus a random (or fixed) salt is fed through PBKDF2-HMAC-SHA256 to produce a 64-byte master key.
2. **Wordmap (optional).** If you supply a JSON wordmap, whole-word matches in the plaintext are rewritten first (e.g. `"attack" -> "sunrise"`). This is steganographic padding, not cryptography.
3. **Vigenere stream.** The (possibly rewritten) plaintext is XOR-ed against a keystream derived from the master key.
4. **Alphabet encoding.** The resulting byte stream is re-encoded into your chosen alphabet.
5. **HMAC tag.** An HMAC-SHA256 tag over the ciphertext is appended; decrypt verifies it before returning plaintext.

For a deeper walk-through, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Security caveats

`retlang` is an educational, toy-grade secret language. It is strong enough to stop a casual reader, a snooping sibling, or a coworker glancing at your screen. It is **not** strong enough to stop a motivated cryptanalyst, and it is **not** a replacement for peer-reviewed tools like `age`, `gpg`, or the `cryptography` library. The new alphabets and strength levels do not change that; they raise the effort a casual attacker needs, not the floor a professional one would hit.

Do not use `retlang` for:

- Health, financial, or legal secrets.
- Anything that would harm you or someone else if broken.
- Long-term archival of sensitive material.

For the full honest threat model, recommended alternatives, and disclosure policy, read [docs/SECURITY.md](docs/SECURITY.md).

## Development

```bash
# Run the test suite
python -m unittest discover tests

# Install in editable mode while hacking
pip install -e .
```

All tests are stdlib `unittest`. No pytest, no tox, no matrix. If you add a feature, add a test next to it and keep the existing ones green.

## License

MIT. See [LICENSE](LICENSE).

This project is maintained by a single person in their spare time. Issues and pull requests are welcome but may receive sporadic responses; please read [CONTRIBUTING.md](CONTRIBUTING.md) before filing.

Homepage and issue tracker: <https://github.com/SanjaySparker27/retlang>
