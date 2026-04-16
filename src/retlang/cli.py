"""Command-line interface for retlang.

Subcommands:
    encrypt          encrypt a message
    decrypt          decrypt a message
    genkey           print a fresh random 32-char passphrase
    list-alphabets   print the available alphabet profiles
    share            encrypt and emit a retlang:// URL
    open             decrypt a retlang:// URL
    ui               launch the local web UI
    agent            watch the clipboard for retlang:// URLs
    suggest-phrase   diceware-style passphrase suggestion
    strength-check   score a passphrase (entropy, verdict)
"""

from __future__ import annotations

import argparse
import getpass
import json
import secrets
import sys
from typing import Dict, Optional

from . import agent as _agent
from . import ui as _ui
from .alphabets import alphabet_preview, list_alphabets, NAME_TO_ID
from .cipher import decrypt, encrypt
from .entropy import format_report
from .keyderivation import DEFAULT_STRENGTH, STRENGTH_ITERATIONS
from .phrase import phrase_entropy_bits, suggest_phrase, wordlist_size
from .share import open_url, share


def _read_input(args: argparse.Namespace) -> str:
    if getattr(args, "input", None):
        with open(args.input, "r", encoding="utf-8") as fh:
            return fh.read()
    message = getattr(args, "message", None)
    if message is not None:
        return message
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise SystemExit("error: no input provided. Pass a message, -i FILE, or pipe stdin.")


def _write_output(args: argparse.Namespace, data: str) -> None:
    if getattr(args, "output", None):
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(data)
    else:
        sys.stdout.write(data)
        if not data.endswith("\n"):
            sys.stdout.write("\n")


def _load_wordmap(path: Optional[str]) -> Optional[Dict[str, str]]:
    if not path:
        return None
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise SystemExit(f"error: wordmap file {path} must contain a JSON object")
    result: Dict[str, str] = {}
    for key, value in data.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise SystemExit("error: wordmap entries must be string -> string")
        result[key] = value
    return result


def _resolve_passphrase(args: argparse.Namespace, prompt: str = "Passphrase: ") -> str:
    if getattr(args, "passphrase", None):
        return args.passphrase
    try:
        return getpass.getpass(prompt)
    except (EOFError, KeyboardInterrupt):
        raise SystemExit("error: passphrase required")


# ------------------------------------------------------------------
# Subcommand implementations
# ------------------------------------------------------------------

def _cmd_encrypt(args: argparse.Namespace) -> int:
    plaintext = _read_input(args)
    passphrase = _resolve_passphrase(args)
    wordmap = _load_wordmap(args.wordmap)
    ciphertext = encrypt(
        plaintext,
        passphrase,
        alphabet=args.alphabet,
        wordmap=wordmap,
        iterations=args.iterations,
        strength=args.strength,
    )
    _write_output(args, ciphertext)
    return 0


def _cmd_decrypt(args: argparse.Namespace) -> int:
    ciphertext = _read_input(args)
    passphrase = _resolve_passphrase(args)
    wordmap = _load_wordmap(args.wordmap)
    ciphertext = ciphertext.rstrip("\n")
    try:
        plaintext = decrypt(
            ciphertext,
            passphrase,
            alphabet=args.alphabet,
            wordmap=wordmap,
        )
    except Exception as exc:
        print(f"decryption failed: {exc}", file=sys.stderr)
        return 2
    _write_output(args, plaintext)
    return 0


def _cmd_genkey(args: argparse.Namespace) -> int:
    length = args.length
    byte_count = max(24, length)
    key = secrets.token_urlsafe(byte_count)[:length]
    sys.stdout.write(key + "\n")
    return 0


def _cmd_list_alphabets(args: argparse.Namespace) -> int:
    sys.stdout.write(f"{'name':<14s}  {'id':>2s}  preview\n")
    sys.stdout.write(f"{'-'*14}  {'-'*2}  {'-'*20}\n")
    for name in list_alphabets():
        preview = alphabet_preview(name, 16)
        sys.stdout.write(f"{name:<14s}  {NAME_TO_ID[name]:>2d}  {preview}\n")
    return 0


def _cmd_share(args: argparse.Namespace) -> int:
    plaintext = _read_input(args)
    passphrase = _resolve_passphrase(args)
    wordmap = _load_wordmap(args.wordmap)
    try:
        url = share(
            plaintext,
            passphrase,
            wordmap=wordmap,
            strength=args.strength,
        )
    except Exception as exc:
        print(f"share failed: {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(url + "\n")
    return 0


def _cmd_open(args: argparse.Namespace) -> int:
    url = args.url
    if url is None:
        if not sys.stdin.isatty():
            url = sys.stdin.read().strip()
        else:
            raise SystemExit("error: no URL provided")
    passphrase = _resolve_passphrase(args)
    wordmap = _load_wordmap(args.wordmap)
    try:
        plaintext = open_url(url, passphrase, wordmap=wordmap)
    except Exception as exc:
        print(f"open failed: {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(plaintext)
    if not plaintext.endswith("\n"):
        sys.stdout.write("\n")
    return 0


def _cmd_ui(args: argparse.Namespace) -> int:
    _ui.launch(port=args.port, open_browser=not args.no_browser)
    return 0


def _cmd_agent(args: argparse.Namespace) -> int:
    if args.once:
        # Convenience mode: block on the next URL, decrypt once, exit.
        def _one_shot(url: str) -> None:
            sys.stderr.write("retlang URL detected in clipboard.\n")
            passphrase = _resolve_passphrase(args)
            try:
                plaintext = open_url(url, passphrase)
            except Exception as exc:
                print(f"decryption failed: {exc}", file=sys.stderr)
                raise SystemExit(2)
            sys.stdout.write(plaintext)
            if not plaintext.endswith("\n"):
                sys.stdout.write("\n")

        _agent.watch(_one_shot, interval=0.5, once=True)
        return 0
    _agent.agent_cli()
    return 0


def _cmd_suggest_phrase(args: argparse.Namespace) -> int:
    phrase = suggest_phrase(words=args.words, separator=args.separator)
    bits = phrase_entropy_bits(args.words, wordlist_size())
    sys.stdout.write(phrase + "\n")
    sys.stderr.write(
        f"[{args.words} words ~ {bits:.1f} bits of entropy]\n"
    )
    return 0


def _cmd_strength_check(args: argparse.Namespace) -> int:
    if args.passphrase is not None:
        pw = args.passphrase
    elif args.pass_arg is not None:
        pw = args.pass_arg
    else:
        try:
            pw = getpass.getpass("Passphrase: ")
        except (EOFError, KeyboardInterrupt):
            raise SystemExit("error: passphrase required")
    sys.stdout.write(format_report(pw))
    return 0


# ------------------------------------------------------------------
# Parser
# ------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="retlang",
        description="Two-way tamper-evident secret-language encryption (retlang).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("-p", "--passphrase", help="passphrase (prompted if omitted)")
        sp.add_argument(
            "-a",
            "--alphabet",
            default="base64",
            choices=list_alphabets(),
            help="alphabet profile (default: base64)",
        )
        sp.add_argument("-m", "--wordmap", help="path to JSON wordmap file")
        sp.add_argument("-i", "--input", help="read input from file instead of argument")
        sp.add_argument("-o", "--output", help="write output to file instead of stdout")
        sp.add_argument("message", nargs="?", help="message text (if not using -i)")

    # encrypt
    sp_enc = subparsers.add_parser("encrypt", help="encrypt a message (retlang)")
    add_common(sp_enc)
    strength_group = sp_enc.add_mutually_exclusive_group()
    strength_group.add_argument(
        "-s",
        "--strength",
        default=None,
        choices=sorted(STRENGTH_ITERATIONS),
        help=(
            f"named strength level (default: {DEFAULT_STRENGTH}). "
            "Mutually exclusive with --iterations."
        ),
    )
    strength_group.add_argument(
        "--iterations",
        type=int,
        default=None,
        help=(
            "PBKDF2 iterations as an integer. Mutually exclusive with "
            "-s/--strength. Advanced override."
        ),
    )
    sp_enc.set_defaults(func=_cmd_encrypt)

    # decrypt
    sp_dec = subparsers.add_parser("decrypt", help="decrypt a message (retlang)")
    add_common(sp_dec)
    sp_dec.set_defaults(func=_cmd_decrypt)

    # genkey
    sp_key = subparsers.add_parser("genkey", help="print a random passphrase")
    sp_key.add_argument(
        "-n",
        "--length",
        type=int,
        default=32,
        help="passphrase length in characters (default: 32)",
    )
    sp_key.set_defaults(func=_cmd_genkey)

    # list-alphabets
    sp_list = subparsers.add_parser(
        "list-alphabets",
        help="list the available retlang alphabet profiles",
    )
    sp_list.set_defaults(func=_cmd_list_alphabets)

    # share
    sp_share = subparsers.add_parser(
        "share",
        help="encrypt and emit a retlang:// URL for one-click sharing",
    )
    sp_share.add_argument("-p", "--passphrase", help="passphrase (prompted if omitted)")
    sp_share.add_argument(
        "-s",
        "--strength",
        default="normal",
        choices=sorted(STRENGTH_ITERATIONS),
        help="named strength level (default: normal)",
    )
    sp_share.add_argument("-m", "--wordmap", help="path to JSON wordmap file")
    sp_share.add_argument("-i", "--input", help="read input from file instead of argument")
    sp_share.add_argument("message", nargs="?", help="message text (if not using -i)")
    sp_share.set_defaults(func=_cmd_share)

    # open
    sp_open = subparsers.add_parser(
        "open",
        help="decrypt a retlang:// URL (pair with `share`)",
    )
    sp_open.add_argument("-p", "--passphrase", help="passphrase (prompted if omitted)")
    sp_open.add_argument("-m", "--wordmap", help="path to JSON wordmap file")
    sp_open.add_argument("url", nargs="?", help="retlang:// URL (or pipe via stdin)")
    sp_open.set_defaults(func=_cmd_open)

    # ui
    sp_ui = subparsers.add_parser(
        "ui",
        help="launch the local web UI (binds to 127.0.0.1 only)",
    )
    sp_ui.add_argument(
        "--port", type=int, default=8787, help="port to bind (default: 8787)"
    )
    sp_ui.add_argument(
        "--no-browser",
        action="store_true",
        help="do not auto-open a browser window",
    )
    sp_ui.set_defaults(func=_cmd_ui)

    # agent
    sp_agent = subparsers.add_parser(
        "agent",
        help="watch the clipboard and decrypt retlang:// URLs as they appear",
    )
    sp_agent.add_argument("-p", "--passphrase", help="passphrase (prompted if omitted)")
    sp_agent.add_argument(
        "--once",
        action="store_true",
        help="exit after the first detected URL",
    )
    sp_agent.set_defaults(func=_cmd_agent)

    # suggest-phrase
    sp_sp = subparsers.add_parser(
        "suggest-phrase",
        help="print a diceware-style passphrase (bits on stderr)",
    )
    sp_sp.add_argument(
        "--words", type=int, default=6, help="number of words (default: 6)"
    )
    sp_sp.add_argument(
        "--separator", default="-", help="separator between words (default: '-')"
    )
    sp_sp.set_defaults(func=_cmd_suggest_phrase)

    # strength-check
    sp_sc = subparsers.add_parser(
        "strength-check",
        help="score a passphrase's strength (entropy, verdict, notes)",
    )
    sp_sc.add_argument(
        "pass_arg",
        nargs="?",
        default=None,
        help="passphrase as positional (or use -p)",
    )
    sp_sc.add_argument(
        "-p", "--passphrase", default=None, help="passphrase (prompted if omitted)"
    )
    sp_sc.set_defaults(func=_cmd_strength_check)

    return parser


def main(argv: Optional[list] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
