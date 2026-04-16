# Security Policy

Thanks for helping keep retlang and its users safe. This document describes
which versions receive security fixes and how to report a vulnerability.

> A more detailed threat model and cryptographic notes live in
> [`docs/SECURITY.md`](docs/SECURITY.md). This file is the top-level policy
> that GitHub surfaces in the repository's **Security** tab.

## Supported versions

| Version | Status        |
| ------- | ------------- |
| 0.2.x   | Supported     |
| 0.1.x   | Not supported |

Older pre-release versions receive no fixes. Please upgrade to the latest
`0.2.x` release before reporting.

## Reporting a vulnerability

**Do not open a public GitHub issue for security bugs.**

Use GitHub's **private vulnerability reporting** for this repository:

1. Go to the repository's **Security** tab.
2. Click **Advisories** -> **Report a vulnerability**.
3. Fill in the form with reproduction steps and the affected version.

Direct link:
<https://github.com/SanjaySparker27/retlang/security/advisories/new>

### What to include

- Affected version (`python -c "import retlang; print(retlang.__version__)"`)
- Python version and operating system
- A minimal reproduction (code or CLI invocation), with any secrets redacted
- Your assessment of impact (confidentiality, integrity, availability)

### Response and disclosure

- We aim to acknowledge new reports within a few business days.
- We operate on a **90-day disclosure window** by default: if a fix is not
  released within 90 days of the initial report, the reporter is free to
  publish details. We will ask for an extension only if a fix is in flight.
- Once a fix ships, the advisory will be published via GitHub Security
  Advisories and referenced from `CHANGELOG.md`.

## Scope

retlang is described as **toy-grade secret-language encryption**. It is not a
replacement for vetted cryptography (AES-GCM, libsodium, age, etc.) and is not
intended for protecting data against motivated attackers. Reports that
essentially restate this design limitation are out of scope.

In-scope examples:

- Memory-corruption-style bugs in the Python code (crashes, hangs).
- Logic errors that cause silent data loss or incorrect decryption.
- Tamper-evidence bypasses inside the documented threat model.
- Supply-chain issues in the release pipeline (wheel tampering, workflow
  injection, etc.).

Out-of-scope examples:

- "The cipher is weak" -- this is documented; see `docs/SECURITY.md`.
- Attacks that require the attacker to already control the user's machine.
- Vulnerabilities only in third-party optional extras (report those upstream).

## Bounty

There is no paid bug bounty. Valid reports receive credit in `CHANGELOG.md`
and, at the reporter's option, in the published GitHub Security Advisory.
