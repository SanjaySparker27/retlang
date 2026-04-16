# retlang

Turn ordinary text into a whispered dialect of symbols, emoji, and glyphs — with authenticated integrity, shareable links, and a local browser UI.

[![PyPI version](https://img.shields.io/pypi/v/retlang.svg)](https://pypi.org/project/retlang/)
[![Python versions](https://img.shields.io/pypi/pyversions/retlang.svg)](https://pypi.org/project/retlang/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![CI](https://github.com/SanjaySparker27/retlang/actions/workflows/ci.yml/badge.svg)](https://github.com/SanjaySparker27/retlang/actions/workflows/ci.yml)
[![GitHub stars](https://img.shields.io/github/stars/SanjaySparker27/retlang.svg?style=social)](https://github.com/SanjaySparker27/retlang)

`retlang` is a Python 3 library and CLI that turns plaintext into a reversible, stylized ciphertext using passphrase-derived keys. It ships with 11 output alphabets, 4 strength presets, shareable `retlang://` URLs, a local browser UI, and a clipboard watcher. The core has zero runtime dependencies and never touches the network — nothing leaves your machine unless you paste it somewhere.

## Quick start

```bash
pip install retlang

retlang suggest-phrase                      # generate a strong passphrase
retlang share -p "hunter2 table cloud" "meet at 8"
# -> retlang://v1/<base64url>
```

On the receiving side:

```bash
retlang open "retlang://v1/<base64url>"     # prompts for passphrase
# meet at 8
```

## Browser UI

`retlang ui` spins up a local web app on `http://127.0.0.1:8765`. Drag-drop a note, pick an alphabet, watch the entropy meter move, and copy the resulting `retlang://` link or QR code.

<!-- Placeholder: drop a real screenshot here. Do not commit the image from this PR. -->
![retlang browser UI](docs/screenshot-ui.png)

Features:

- Drag-drop plaintext or ciphertext.
- Live alphabet preview as you type the passphrase.
- Entropy meter and strength scoring for the passphrase.
- QR code for the resulting `retlang://` link.
- Copy-to-clipboard share link.

The server binds to `127.0.0.1` only. It does not expose itself on your LAN. Nothing leaves your machine.

## Features

- 11 alphabet profiles: `base64`, `letters`, `numbers`, `symbols`, `emoji-smiley`, `emoji-animals`, `emoji-food`, `emoji-nature`, `geometric`, `runes`, `astro`.
- 4 strength presets with PBKDF2-HMAC-SHA256:

  | Preset     | Iterations |
  |------------|-----------:|
  | `fast`     |    100,000 |
  | `normal`   |    200,000 |
  | `strong`   |    500,000 |
  | `paranoid` |  1,000,000 |

- Shareable `retlang://v1/<base64url>` URLs (`retlang share`, `retlang open`).
- Local browser UI (`retlang ui`) that stays on `127.0.0.1`; nothing leaves your machine.
- Clipboard agent mode (`retlang agent`) that auto-decrypts `retlang://` links as they land in your clipboard.
- Diceware passphrase generator backed by an EFF-style wordlist (`retlang suggest-phrase`).
- Entropy meter and strength scoring (`retlang strength-check`).
- QR code output (optional: `pip install retlang[qr]`).
- Tamper-evident HMAC-SHA256 integrity tag on every envelope.
- Zero runtime dependencies for the core library.

## How it works

```
plaintext
  -> optional wordmap layer
  -> keyed Vigenere byte shift   <- key from PBKDF2-HMAC-SHA256(passphrase, salt, N)
  -> envelope (magic | version | iters | salt | alphabet_id | ciphertext)
  -> HMAC-SHA256 tag appended
  -> alphabet encode
  -> ciphertext / retlang:// URL
```

For the full pipeline, module contracts, and envelope format, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Security

`retlang` is a toy-grade secret language. It protects notes from casual readers and tampering, but it is **not** a replacement for [`age`](https://age-encryption.org/), GPG, or authenticated AEAD primitives like AES-GCM. If the data matters, use a real tool.

Two security documents live in this repo and cover different things:

- [docs/SECURITY.md](docs/SECURITY.md) — threat model, honest caveats, what retlang does and does not defend against.
- [SECURITY.md](SECURITY.md) (top-level) — vulnerability disclosure policy for GitHub.

Read both before trusting `retlang` with anything you would not write on a postcard.

## Install

```bash
# Core, stdlib-only
pip install retlang

# With QR code support
pip install retlang[qr]

# Everything optional enabled
pip install retlang[all]

# Bleeding edge from GitHub
pip install git+https://github.com/SanjaySparker27/retlang.git
```

Python 3.10 or newer is required.

## Commands

| Command                   | Purpose                                                                 |
|---------------------------|-------------------------------------------------------------------------|
| `retlang encrypt`         | Encrypt a plaintext to ciphertext in a chosen alphabet.                 |
| `retlang decrypt`         | Decrypt ciphertext back to plaintext (alphabet auto-detected).          |
| `retlang share`           | Encrypt and wrap the envelope as a `retlang://v1/...` URL.              |
| `retlang open`            | Open a `retlang://` URL and print the plaintext.                        |
| `retlang ui`              | Launch the local browser UI on `127.0.0.1`.                             |
| `retlang agent`           | Watch the clipboard and auto-decrypt `retlang://` links.                |
| `retlang suggest-phrase`  | Generate a diceware passphrase from the EFF-style wordlist.             |
| `retlang strength-check`  | Score a passphrase for bits of entropy and return a verdict.            |
| `retlang genkey`          | Emit a random passphrase (alnum, hex, or words).                        |
| `retlang list-alphabets`  | List every registered output alphabet with a preview.                   |

Run `retlang <command> --help` for full flag details, or see [docs/USAGE.md](docs/USAGE.md).

## Development

```bash
git clone https://github.com/SanjaySparker27/retlang.git
cd retlang
pip install -e ".[dev]"
python -m unittest discover tests
retlang ui   # try the UI locally
```

All tests run on stdlib `unittest`. No pytest, no tox, no matrix.

## Contributing

Issues and pull requests are welcome. Before opening a PR, read [CONTRIBUTING.md](CONTRIBUTING.md) and the [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

This project is maintained by a single person in their spare time. Reviews may be sporadic; please keep PRs small and focused.

## License

MIT. See [LICENSE](LICENSE).

Homepage and issue tracker: <https://github.com/SanjaySparker27/retlang>
