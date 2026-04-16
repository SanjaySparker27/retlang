# Security Policy and Threat Model

> **Scope note.** This file is the project's *threat model* and honest caveats document. For the vulnerability disclosure policy (how to report a bug privately, response SLAs, coordinated-disclosure timelines), see the top-level [`SECURITY.md`](../SECURITY.md) instead. Both files exist on purpose: this one tells you what `retlang` can and cannot defend against; the top-level one tells you what to do when you think you've found a flaw.

`retlang` is a toy cipher. This document is an honest description of what it can and cannot do, so you can decide whether it is appropriate for your use case.

## TL;DR

- `retlang` protects plaintext from casual readers.
- `retlang` does **not** protect plaintext from cryptanalysts, state-level attackers, or anyone running a serious attack.
- If you need real cryptography, use [`age`](https://age-encryption.org/), [GnuPG](https://www.gnupg.org/), or the Python [`cryptography`](https://cryptography.io/) library instead.

## Threat model

### What `retlang` is intended to defend against

- Someone glancing over your shoulder at a terminal.
- A family member, roommate, or coworker casually opening a file on a shared machine.
- A journal or diary stored in a private repo that you would prefer even privileged readers could not skim at a glance.
- Offline puzzles, escape rooms, ARGs, and classroom exercises about substitution ciphers.
- Steganographic flavor: making a message look like a weather report, a horoscope, or a string of emoji.

Against all of the above, `retlang` works well. A passphrase-derived key plus an HMAC tag reliably prevents the kinds of reader who will not run software to break it.

### What `retlang` is **not** intended to defend against

- A cryptanalyst with any budget. Vigenere-style stream ciphers are known-plaintext fragile and do not match the security properties of AES-GCM or ChaCha20-Poly1305.
- Side-channel attacks (timing, cache, power). `retlang` makes no constant-time guarantees.
- An attacker who can observe many ciphertexts produced with the same passphrase. The security margin degrades with reuse.
- An attacker with access to your passphrase. There is no forward secrecy.
- Anyone who can modify the `retlang` source on your machine.
- Anyone running a serious cryptographic attack. Period.

### Explicit non-goals

`retlang` is **not** suitable for:

- Health records, banking information, tax documents, legal communications.
- Passwords, API keys, cloud credentials.
- Anything whose disclosure could harm you, your employer, or a third party.
- Long-term archival of material you care about.
- Any regulated-data workflow (HIPAA, PCI-DSS, GDPR sensitive categories, etc.).
- Activism, journalism, or any scenario where a powerful adversary is in the threat model. Use [Signal](https://signal.org/) and [age](https://age-encryption.org/) instead, please.

If you are unsure whether your use case is safe for `retlang`, assume it is not, and pick a real tool.

## Why you should use `age`, `gpg`, or `cryptography` for real secrets

- [`age`](https://age-encryption.org/) is a modern, audited file-encryption tool with small keys, a simple CLI, and no configuration knobs to misuse. Best default choice for "encrypt this file."
- [GnuPG](https://www.gnupg.org/) is older and more complex but ubiquitous; pick it when you need interoperability with existing PGP users.
- The Python [`cryptography`](https://cryptography.io/) library (specifically `Fernet` or `AEAD` primitives) is the right building block if you are writing Python and need authenticated encryption with sensible defaults.

All three are peer-reviewed, maintained by teams, and have undergone external audits. `retlang` is none of those things, and pretending otherwise would be dishonest.

## What `retlang` does get right

For the avoidance of doubt, here is what `retlang` does correctly:

- Keys are derived with PBKDF2-HMAC-SHA256, not used raw.
- A random salt is generated per encryption unless the caller pins one.
- Every ciphertext carries an HMAC-SHA256 tag; tampered messages fail to decrypt.
- No plaintext is ever returned on a failed integrity check.
- No third-party dependencies means a smaller supply-chain surface than most alternatives.

These make `retlang` meaningfully better than rot13 or naive Vigenere. They do not make it AES-GCM.

## Reporting a vulnerability

If you believe you have found a security issue in `retlang`, please do **not** open a public GitHub issue at <https://github.com/SanjaySparker27/retlang/issues>. Instead, email the maintainer privately:

**security@example.com**

> Note: this is still a placeholder address. The project now has a real repository at <https://github.com/SanjaySparker27/retlang>; the maintainer email will be published there once set up. Until then, please use GitHub's private vulnerability reporting on that repo.

Please include:

- A description of the issue and its impact.
- Steps or code to reproduce.
- Any suggested mitigation, if you have one.

Expect an initial acknowledgment within seven days. Since this project has a solo maintainer, fixes may take longer than the ninety-day industry norm; please be patient. If the issue is severe enough that public disclosure is warranted before a fix ships, we will coordinate with you on a timeline.

## Known vulnerabilities

None at this time. `retlang` is a new project; there are no filed CVEs against it.

This does not mean there are none to find. It means nobody has found any yet. Given the explicit threat model above, "no known vulnerabilities" should not be read as "audited and approved for sensitive data." It should be read as "the maintainer has not been told about any bugs, and neither has anyone else publicly."

## Supported versions

Only the latest `main` branch and the most recent tagged release receive security fixes. Older tags are frozen in time. If you are running an older version, upgrade before reporting issues.

## v0.2.0 additional caveats

Version 0.2.0 adds a local browser UI, shareable URLs, and a clipboard watcher. None of these change the underlying threat model, but they do introduce a few surfaces worth calling out explicitly.

- **Local browser UI (`retlang ui`) binds to `127.0.0.1` only.** It is not reachable from your LAN, from a VPN peer, or from any other host. There is no CLI flag to listen on `0.0.0.0`. Even so, the UI trusts whoever can reach `127.0.0.1` on your machine — that means any local user, any local process, and any locally compromised browser extension. You are responsible for ensuring the machine itself is trusted; `retlang` cannot help with that.
- **`retlang://` URLs are ciphertext, not plaintext — but they are still interceptable.** If you send a `retlang://` link over an insecure channel (unencrypted email, a group chat you don't trust, a social media DM), the ciphertext is exposed to anyone watching that channel. The HMAC tag will detect tampering, but it cannot detect interception. An attacker who captures the URL can then brute-force the passphrase offline, limited by your chosen PBKDF2 iteration count. Use a strong passphrase and a trusted transport.
- **Clipboard watcher (`retlang agent`) reads the system clipboard via subprocess.** It only acts on strings starting with `retlang://` and never logs or transmits anything, but the clipboard itself is a shared OS resource: other processes on the same machine can read it too. If you paste a plaintext into your clipboard to encrypt it, that plaintext is briefly visible to any process with clipboard access until you copy something else.
- **QR codes are just URLs in image form.** A QR code of a `retlang://` link has the same security properties as the URL: anyone who can photograph the code can attempt offline brute-force. Do not paste QR codes into public screenshares.
