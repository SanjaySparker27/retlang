"""Command-line interface for retlang.

Subcommands:
    encrypt         encrypt a message
    decrypt         decrypt a message
    genkey          print a fresh random 32-char passphrase
    list-alphabets  print the available alphabet profiles
"""

from __future__ import annotations

import argparse
import getpass
import json
import secrets
import sys
from typing import Dict, Optional

from .alphabets import alphabet_preview, list_alphabets, NAME_TO_ID
from .cipher import decrypt, encrypt
from .keyderivation import DEFAULT_STRENGTH, STRENGTH_ITERATIONS


def _read_input(args: argparse.Namespace) -> str:
    if args.input:
        with open(args.input, "r", encoding="utf-8") as fh:
            return fh.read()
    if args.message is not None:
        return args.message
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise SystemExit("error: no input provided. Pass a message, -i FILE, or pipe stdin.")


def _write_output(args: argparse.Namespace, data: str) -> None:
    if args.output:
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


def _resolve_passphrase(args: argparse.Namespace) -> str:
    if args.passphrase:
        return args.passphrase
    try:
        return getpass.getpass("Passphrase: ")
    except (EOFError, KeyboardInterrupt):
        raise SystemExit("error: passphrase required")


def _cmd_encrypt(args: argparse.Namespace) -> int:
    plaintext = _read_input(args)
    passphrase = _resolve_passphrase(args)
    wordmap = _load_wordmap(args.wordmap)
    # argparse enforces mutual exclusion between --iterations and -s/--strength.
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
    # Strip a single trailing newline if the input came from a file/stdin.
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
    # token_urlsafe returns ~1.3 chars per byte; pick a byte count that
    # yields at least `length` characters, then slice.
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

    sp_enc = subparsers.add_parser("encrypt", help="encrypt a message (retlang)")
    add_common(sp_enc)
    # Strength vs. iterations are mutually exclusive. argparse enforces it.
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

    sp_dec = subparsers.add_parser("decrypt", help="decrypt a message (retlang)")
    add_common(sp_dec)
    sp_dec.set_defaults(func=_cmd_decrypt)

    sp_key = subparsers.add_parser("genkey", help="print a random passphrase")
    sp_key.add_argument(
        "-n",
        "--length",
        type=int,
        default=32,
        help="passphrase length in characters (default: 32)",
    )
    sp_key.set_defaults(func=_cmd_genkey)

    sp_list = subparsers.add_parser(
        "list-alphabets",
        help="list the available retlang alphabet profiles",
    )
    sp_list.set_defaults(func=_cmd_list_alphabets)

    return parser


def main(argv: Optional[list] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
