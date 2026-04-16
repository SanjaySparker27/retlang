# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-04-16

### Added

- Local browser UI served by `retlang ui`. Binds to `127.0.0.1` only; drag-drop plaintext or ciphertext, live alphabet preview, entropy meter, QR code, copy-to-clipboard share link.
- Shareable URL format `retlang://v1/<base64url>` with the `retlang share` and `retlang open` subcommands. The envelope bytes are wrapped in url-safe base64 (no padding) for transport.
- Clipboard watcher `retlang agent` that auto-decrypts `retlang://` links as they land in the clipboard. Cross-platform via `pbpaste` / `xclip` / `wl-paste` / `Get-Clipboard`. Supports `--once` for a single pass.
- Diceware passphrase generator `retlang suggest-phrase` backed by an EFF-style wordlist bundled at `wordlists/eff_large.txt`. `--words N` selects length.
- Entropy scoring command `retlang strength-check`, returning `{bits, score, verdict, notes}`.
- Six new alphabet profiles: `letters`, `numbers`, `symbols`, `emoji-animals`, `emoji-food`, `emoji-nature`. Eleven profiles ship in total.
- Four strength presets: `fast` (100k), `normal` (200k), `strong` (500k), `paranoid` (1M) PBKDF2 iterations.
- `--iterations INT` advanced override for pinning a custom PBKDF2 iteration count. Mutually exclusive with `-s/--strength`.
- Optional QR code output via the `[qr]` extra. Install with `pip install retlang[qr]`.
- New modules: `share.py`, `phrase.py`, `entropy.py`, `qr.py`, `agent.py`, `ui.py`. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the contract of each.

### Changed

- Alphabet IDs renumbered to `0..10` to accommodate the six new profiles.
- Envelope `VERSION` byte bumped from `0x01` to `0x02`. v1 envelopes still decrypt.
- `emoji` alphabet renamed to `emoji-smiley`. The old name is preserved as an alias so existing scripts keep working.
- Package version bumped from `0.1.0` to `0.2.0`.

### Deprecated

- Alphabet name `emoji` — use `emoji-smiley`. The alias is kept for backward compatibility but may be removed in a future major release.

### Security

- All randomness sourced from `secrets`, never `random`.
- HMAC verified via `hmac.compare_digest` before any layer is reversed on decrypt.
- Browser UI binds strictly to `127.0.0.1`; no LAN exposure.

## [0.1.0] - 2026-04-16

### Added

- Initial public release.
- Core cipher pipeline: PBKDF2-HMAC-SHA256 key derivation, keyed Vigenere byte shift, optional wordmap substitution, HMAC-SHA256 tag.
- Five output alphabets: `base64`, `emoji`, `geometric`, `runes`, `astro`.
- CLI with subcommands `encrypt`, `decrypt`, `genkey`, `list-alphabets`.
- Optional wordmap layer for steganographic flavor.
- Unit, integration, and tamper-detection test suites on stdlib `unittest`.

[0.2.0]: https://github.com/SanjaySparker27/retlang/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/SanjaySparker27/retlang/releases/tag/v0.1.0
