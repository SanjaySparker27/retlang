# Contributing to retlang

Thanks for your interest in `retlang`. Before you open an issue or a pull request, please read the notes below so your time is well spent.

The canonical repository is <https://github.com/SanjaySparker27/retlang>. Issues, pull requests, and discussions all live there.

## Solo maintainer notice

`retlang` is maintained by one person in their spare time. There is no team, no on-call rotation, and no service-level agreement. This has a few practical consequences:

- Issues may sit for days or weeks before anyone looks at them. That is not rudeness; it is bandwidth.
- Pull requests are reviewed when time allows. A large PR may take longer than a small one, not because it is worse, but because reviewing it costs more attention.
- Feature requests may be politely declined if they widen the scope of the project. `retlang` aims to stay small.

You are still welcome to contribute. This document explains how to do it in a way that is most likely to get merged.

## How to open a good issue

Before filing, please:

1. Search existing issues (open and closed) to confirm your problem is not already tracked.
2. Confirm you are on the latest `main`; bugs in older tags may already be fixed.
3. Include a minimal reproduction: the exact command or Python snippet, the passphrase you used (or a dummy one), the alphabet, and the observed vs expected output.
4. Include your Python version (`python --version`) and operating system.

Security-sensitive reports should not go in public issues. Follow the disclosure process in [docs/SECURITY.md](docs/SECURITY.md) instead.

## How to open a good pull request

1. **Open an issue first** for anything bigger than a typo fix. A two-line discussion up front saves a two-hundred-line rewrite later.
2. **Keep the scope narrow.** One PR, one concern. Unrelated cleanups belong in a separate PR.
3. **Match the existing style.** `retlang` uses plain Python 3.9+ with type hints where they add clarity. No formatter is enforced, but do not reflow unrelated code.
4. **Write a test.** Every behavior change should include a `unittest` case. Regression tests for bugs are especially welcome.
5. **Run the suite locally before pushing:**

   ```bash
   python -m unittest discover tests
   ```

   All PRs must leave the suite green. CI will check this too.

## Style and dependency policy

- **Standard library only.** This is a firm rule. `retlang` exists partly to demonstrate what the Python stdlib alone can do. PRs that add a runtime dependency will be closed. Dev-time dependencies (linters, formatters) are also discouraged; keep `pyproject.toml` minimal.
- **No dynamic code generation.** `eval`, `exec`, and `__import__` on user input are forbidden.
- **Prefer clarity over cleverness.** If a one-liner needs a comment explaining it, write the five-line version.
- **Docstrings on every public function.** The CLI help text is auto-generated from them.

## What will probably get declined

- Adding `cryptography`, `pycryptodome`, or any other native-extension dependency.
- Replacing the educational cipher with real AES-GCM. That is a different project; use `age` or `cryptography`.
- Breaking the wire format without a version bump and a migration path.
- Feature flags that only one user needs.

## What is very welcome

- Bug fixes with a failing test attached.
- Documentation corrections and clarifications.
- New output alphabets that are unambiguously decodable (64 unique, non-overlapping symbols).
- Performance wins that do not hurt readability.
- Better error messages, especially around passphrase mistakes.

## Running the development version

```bash
git clone https://github.com/SanjaySparker27/retlang.git
cd retlang
pip install -e ".[dev]"
python -m unittest discover tests
retlang ui   # try the UI
```

Editable install plus the `[dev]` extra is the expected setup for contributors. The core stays stdlib-only (see the policy below) but the `[dev]` extra may pull in lint/test helpers — those are fine at dev time, not at runtime.

## Testing philosophy

Tests mirror the module layout under `src/retlang/` and run on stdlib `unittest`. There are four shapes we care about:

- **Unit tests per module.** Every module in `src/retlang/` has a matching test file under `tests/` exercising its public surface. Aim for behavior coverage, not line coverage theater.
- **Integration round-trips.** `tests/test_roundtrip.py` encrypts then decrypts across every alphabet, strength preset, and wordmap combination. If you add an alphabet, layer, or kwarg, extend this file.
- **Tamper rejection.** `tests/test_tamper.py` flips one bit at each field in the envelope (magic, version, iterations, salt, alphabet id, ciphertext, hmac) and asserts that decrypt raises rather than returning plaintext. Any new envelope field must get a tamper case here.
- **UI API smoke tests.** The UI endpoints each get a minimal happy-path plus one failure-path test. These are fast; keep them that way.

All PRs must leave the full suite green. CI enforces this; local runs should match.

## What kinds of changes are accepted

- **New alphabets:** welcome. Requirements: 64 unique, non-overlapping symbols, unambiguous round-trip decode, renders on common terminals and in the browser UI. Add it to `alphabets.BUILTINS` with the next free integer id, extend `tests/layers/test_alphabet.py`, no envelope version bump needed.
- **New layers:** welcome, but they must hide behind a `VERSION` byte bump and must not break decrypt of older envelopes. See `docs/ARCHITECTURE.md` §8.2 for the exact contract.
- **New optional dependencies:** only via a new `[extras]` group in `pyproject.toml`, feature-detected at import time so the core stays importable on a bare stdlib install. See `docs/ARCHITECTURE.md` §15.
- **Core runtime dependencies:** not accepted. The no-runtime-dep rule is load-bearing; it is what keeps the supply chain small and the audit surface tiny.

## License

By submitting a contribution, you agree that your work will be released under the MIT license that covers the rest of the project. See [LICENSE](LICENSE).
