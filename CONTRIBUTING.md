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

## License

By submitting a contribution, you agree that your work will be released under the MIT license that covers the rest of the project. See [LICENSE](LICENSE).
