# retlang — Architecture

> Locked specification. The coder agent MUST implement to this contract.
> Python 3, standard library only. No third-party dependencies.

---

## 1. Overview

`retlang` is a dual-purpose (library + CLI) Python package that produces
authenticated, human-stylized ciphertext. A plaintext string is pushed through
a five-layer pipeline driven by a user passphrase. The output envelope is
self-describing (magic bytes + version + salt + iteration count + alphabet
id) so any compatible `retlang` build can decrypt it given the passphrase.

### 1.1 Design goals

| Goal | How it's met |
|------|--------------|
| Authenticated (no silent tampering) | HMAC-SHA256 tag, verified in constant time, checked **before** any layer is reversed |
| Deterministic under same salt | Pipeline is pure; randomness lives only in salt generation |
| Self-describing output | Versioned header embeds all params needed for decrypt |
| Forward-compatible | `VERSION` byte + `ALPHABET_ID` byte let new layers/alphabets ship without breaking old envelopes |
| Stdlib-only | `hashlib`, `hmac`, `secrets`, `base64`, `argparse`, `getpass`, `json`, `struct` |
| Library-first, CLI-thin | `cli.py` is a 1:1 wrapper over `encrypt()`/`decrypt()` |

### 1.2 Non-goals

- Not a replacement for AES-GCM / age / libsodium. This is a **stylized**
  cipher with authenticated integrity, suitable for puzzles, notes, and
  "secret language" use cases, not high-assurance crypto.
- No key ratcheting, no forward secrecy, no public-key exchange.
- No streaming API in v1 (whole-message encrypt/decrypt only).

---

## 2. Pipeline diagrams

### 2.1 Encrypt

```
  plaintext (str, UTF-8)
        |
        v
  +-----------------+     passphrase
  | keyderivation   | <--- (str)
  |  PBKDF2-HMAC-   |     salt (16B, fresh from secrets.token_bytes)
  |   SHA256        |     iterations (default 200_000)
  +-----------------+
        |
        | derived 64B -> split: cipher_key(32B) || hmac_key(32B)
        v
  +-----------------+
  | layers.vigenere | <--- cipher_key
  | keyed byte shift|
  +-----------------+
        |
        v
  +-----------------+
  | layers.wordmap  | <--- wordmap dict (optional, deterministic)
  | dict substitute |
  +-----------------+
        |
        v
  +-----------------+
  | layers.alphabet | <--- alphabet_id (one of 11 built-in profiles; see §3.10)
  | symbol encode   |
  +-----------------+
        |
        v   ciphertext_bytes
  +-----------------+
  | header.pack     |
  |  MAGIC|VER|ITER |
  |  SALT|ALPHA_ID  |
  +-----------------+
        |
        | header || ciphertext
        v
  +-----------------+
  | integrity.tag   | <--- hmac_key
  |  HMAC-SHA256    |
  +-----------------+
        |
        | header || ciphertext || HMAC(32B)
        v
   base64 / symbol-encode envelope
        |
        v
   output str
```

### 2.2 Decrypt

```
   input str
        |
        v
   base64 / symbol-decode envelope
        |
        v
  +-----------------+
  | header.unpack   |
  |  -> MAGIC check |
  |  -> VER check   |
  |  -> salt, iter, |
  |     alphabet_id |
  +-----------------+
        |
        v   header + ciphertext + tag
  +-----------------+
  | keyderivation   | <--- passphrase + salt + iter
  +-----------------+
        |
        | cipher_key || hmac_key
        v
  +---------------------+
  | integrity.verify    |  <-- FAIL FAST: raise before any layer reversal
  |  hmac.compare_digest|
  +---------------------+
        |
        v
  +-----------------+
  | layers.alphabet |   (decode)
  +-----------------+
        |
        v
  +-----------------+
  | layers.wordmap  |   (reverse substitution)
  +-----------------+
        |
        v
  +-----------------+
  | layers.vigenere |   (reverse byte shift)
  +-----------------+
        |
        v
     plaintext (str, UTF-8)
```

Invariant: `decrypt(encrypt(p, pw)) == p` for all `p`, any `pw`, any supported
alphabet, any (or no) wordmap.

---

## 3. Module reference

Every module lives under `src/retlang/`. Files are kept under 500 lines.
Each module declares a typed public surface; everything else is
underscore-prefixed and treated as private.

### 3.1 `__init__.py`

**Purpose:** Public API entry point. Re-exports `encrypt`, `decrypt`,
`__version__`, and a small set of exceptions.

**Public symbols:**
- `__version__: str`
- `encrypt(plaintext: str, passphrase: str, *, alphabet: str = "base64", wordmap: dict | None = None, strength: str = "normal", iterations: int | None = None) -> str`
- `decrypt(ciphertext: str, passphrase: str, *, wordmap: dict | None = None) -> str`
- `class RetlangError(Exception)` — base class
- `class IntegrityError(RetlangError)` — HMAC mismatch / tamper
- `class HeaderError(RetlangError)` — bad magic / unsupported version
- `class AlphabetError(RetlangError)` — unknown alphabet id / decode failure

**Does NOT:** import from `cli.py`, run any I/O, log.

---

### 3.2 `cipher.py`

**Purpose:** Orchestrate the layer pipeline. This is the only module that
knows the ordering of layers.

**Public functions:**
- `pipeline_encrypt(plaintext: str, cipher_key: bytes, alphabet_id: int, wordmap: dict | None) -> bytes`
- `pipeline_decrypt(ciphertext: bytes, cipher_key: bytes, alphabet_id: int, wordmap: dict | None) -> str`

**Internal responsibilities:**
- UTF-8 encode / decode plaintext at the boundaries.
- Call `vigenere` -> `wordmap` -> `alphabet` on encrypt.
- Call `alphabet` -> `wordmap` -> `vigenere` on decrypt (exact inverse order).
- Route `alphabet_id` through `alphabets.resolve(alphabet_id)`.

**Does NOT:** derive keys, build headers, compute HMAC, touch stdin/stdout.

---

### 3.3 `keyderivation.py`

**Purpose:** PBKDF2 wrapper. Single source of truth for KDF parameters.

**Public functions:**
- `derive(passphrase: str, salt: bytes, iterations: int) -> tuple[bytes, bytes]`
  Returns `(cipher_key, hmac_key)`, each 32 bytes, derived from a single
  `hashlib.pbkdf2_hmac("sha256", ..., dklen=64)` call, then split.
- `new_salt() -> bytes` — exactly 16 bytes from `secrets.token_bytes(16)`.
- `resolve_strength(level: str) -> int` — maps a preset name to an iteration count. Raises `ValueError` on unknown level.
- `DEFAULT_ITERATIONS: int = 200_000`
- `MIN_ITERATIONS: int = 100_000` — `derive()` raises `ValueError` below this.
- `STRENGTH_LEVELS: dict[str, int]` — presets keyed by name:

  | Level      | Iterations |
  |------------|-----------:|
  | `fast`     |    100,000 |
  | `normal`   |    200,000 |
  | `strong`   |    500,000 |
  | `paranoid` |  1,000,000 |

**Does NOT:** cache keys, accept bytes passphrases (passphrase is always
`str`, encoded UTF-8 NFKC internally), log the key.

---

### 3.4 `layers/__init__.py`

**Purpose:** Namespace module. Empty apart from `from . import vigenere, wordmap, alphabet`.

**Does NOT:** export layer functions directly — callers use qualified names.

---

### 3.5 `layers/vigenere.py`

**Purpose:** Keyed byte-shift (Vigenère generalized to 256 bytes).

**Public functions:**
- `encode(data: bytes, key: bytes) -> bytes`
  `out[i] = (data[i] + key[i % len(key)]) mod 256`
- `decode(data: bytes, key: bytes) -> bytes`
  `out[i] = (data[i] - key[i % len(key)]) mod 256`

**Contract:** `decode(encode(x, k), k) == x` for all `x: bytes`, `k: bytes` where `len(k) >= 1`.

**Does NOT:** derive its own key, mutate inputs, handle strings.

---

### 3.6 `layers/wordmap.py`

**Purpose:** Reversible dictionary substitution applied at the string boundary
(before UTF-8 encode on encrypt, after UTF-8 decode on decrypt). Purely
optional — `None` means identity.

**Public functions:**
- `apply(text: str, mapping: dict[str, str]) -> str`
  Replaces every key with its mapped value. Longest-key-first to avoid
  ambiguity. Must be applied consistently token-by-token (not regex-greedy
  across overlaps).
- `reverse(text: str, mapping: dict[str, str]) -> str`
  Uses the inverted mapping. Raises `ValueError` if the mapping is not
  bijective (two keys point to the same value).
- `validate(mapping: dict[str, str]) -> None` — bijectivity + non-empty
  values check. Raises `ValueError` on failure.

**Does NOT:** load files, guess encodings. File loading lives in `cli.py`.

---

### 3.7 `layers/alphabet.py`

**Purpose:** Encode/decode bytes into a stylized symbol alphabet.

**Public functions:**
- `encode(data: bytes, profile: AlphabetProfile) -> str`
- `decode(text: str, profile: AlphabetProfile) -> bytes`
- `class AlphabetProfile` — immutable dataclass: `id: int`, `name: str`,
  `symbols: tuple[str, ...]` (length = 64 for base64-compatible profiles, or
  16/32/256 for other bases the author wires up).

**Encoding:** base-N (N = len(symbols)) positional encoding with `=` padding
rule identical to base64 where applicable. For non-power-of-2 alphabet
sizes, fall back to base-N digit encoding with explicit length prefix.

**Does NOT:** define the symbol tables themselves (that's `alphabets.py`).

---

### 3.8 `header.py`

**Purpose:** Pack and unpack the versioned header. Uses `struct`.

**Public functions:**
- `pack(version: int, iterations: int, salt: bytes, alphabet_id: int) -> bytes`
- `unpack(buf: bytes) -> HeaderFields`
  Raises `HeaderError` on bad magic, unsupported version, or truncated buffer.
- `class HeaderFields` — dataclass:
  `version: int`, `iterations: int`, `salt: bytes`, `alphabet_id: int`,
  `header_size: int` (length of the header prefix — lets callers slice the rest).
- Constants:
  - `MAGIC: bytes = b"SLNG"` — kept for backward compatibility with any v1 envelopes that exist. The magic string does not change when the project is renamed; only the prose around it does.
  - `SUPPORTED_VERSIONS: frozenset[int] = frozenset({1, 2})` — v1 envelopes still decrypt; v2 is the current encrypt target and carries the expanded 11-profile alphabet ID space.
  - `HEADER_SIZE: int = 26` (see §4)

**Does NOT:** read/write files, base64-encode.

---

### 3.9 `integrity.py`

**Purpose:** HMAC tag compute + constant-time verification.

**Public functions:**
- `tag(key: bytes, message: bytes) -> bytes` — 32-byte HMAC-SHA256.
- `verify(key: bytes, message: bytes, expected: bytes) -> None`
  Raises `IntegrityError` on mismatch. Uses `hmac.compare_digest`.

**Contract:** `verify` MUST be called before any decode step in `decrypt()`.

**Does NOT:** derive the hmac key, log the tag.

---

### 3.10 `alphabets.py`

**Purpose:** Built-in symbol profiles. Source of truth for `alphabet_id <-> symbol table`.

**Public functions / data:**
- `BUILTINS: dict[str, AlphabetProfile]` — keyed by human name. v2 envelopes use the following eleven-profile ID layout (v1 envelopes used a different, narrower layout; the `VERSION` byte tells decrypt which table to consult — see §4.4 and §8.2):

  | ID | Name             | Size | Notes                                                      |
  |----|------------------|------|------------------------------------------------------------|
  | 0  | `base64`         | 64   | RFC 4648 URL-safe alphabet, default.                       |
  | 1  | `letters`        | 26 pairs | A-Z pairs, 2 chars per 6-bit group.                    |
  | 2  | `numbers`        | `00`-`63` pairs | 2 chars per 6-bit group.                        |
  | 3  | `symbols`        | 64   | Punctuation-only, 1 char per group, ASCII-safe.            |
  | 4  | `emoji-smiley`   | 64   | Curated face emoji. Legacy name `emoji` aliases to this.   |
  | 5  | `emoji-animals`  | 64   | Curated animal emoji.                                      |
  | 6  | `emoji-food`     | 64   | Curated food emoji.                                        |
  | 7  | `emoji-nature`   | 64   | Curated plants, weather, landscape emoji.                  |
  | 8  | `geometric`      | 64   | Geometric Unicode symbols.                                 |
  | 9  | `runes`          | 64   | Elder Futhark + Younger Futhark + filler.                  |
  | 10 | `astro`          | 64   | Astrological / zodiac / planetary glyphs.                  |

- `ALIASES: dict[str, str]` — `{"emoji": "emoji-smiley"}`. `resolve("emoji")` returns the `emoji-smiley` profile for backward compatibility with pre-v2 callers.
- `resolve(name_or_id: str | int) -> AlphabetProfile`
- `list_names() -> list[str]` — sorted for stable CLI output.

**Does NOT:** mutate at runtime. Profiles are frozen tuples.

---

### 3.11 `cli.py`

**Purpose:** Thin argparse wrapper. See §6 for full contract.

**Public function:**
- `main(argv: list[str] | None = None) -> int` — returns exit code.

**Does NOT:** implement any crypto logic. Every branch ends in a call to
`encrypt()` / `decrypt()` / `alphabets.list_names()` / `keyderivation.new_salt()`.

---

## 4. Data format — the envelope

### 4.1 Binary layout (pre-text-encoding)

```
+--------+--------+---------------+----------+---------------+------------------+----------+
| MAGIC  | VERSION| ITERATIONS    | SALT     | ALPHABET_ID   | CIPHERTEXT       | HMAC     |
| 4B     | 1B     | 4B big-endian | 16B      | 1B            | variable (>=0)   | 32B      |
| "SLNG" | 0x02   | uint32        | random   | uint8         | layered output   | SHA-256  |
+--------+--------+---------------+----------+---------------+------------------+----------+
   0..4     4..5       5..9         9..25        25..26         26..N-32         N-32..N
```

The current encrypt target is `VERSION = 0x02`. `VERSION = 0x01` envelopes (produced before the alphabet ID space was expanded from 5 profiles to 11) still decrypt because their alphabet IDs are resolved through the v1 table; `SUPPORTED_VERSIONS = {1, 2}`. The magic bytes stay `"SLNG"` regardless of the project rename — the magic identifies the envelope format, not the project name.

Total fixed overhead: `4 + 1 + 4 + 16 + 1 + 32 = 58 bytes`, of which the
header is `26 bytes` (offsets 0..26) and the trailing HMAC is `32 bytes`.

### 4.2 HMAC input

```
HMAC_message = MAGIC || VERSION || ITERATIONS || SALT || ALPHABET_ID || CIPHERTEXT
```

i.e. everything except the HMAC field itself. Compute:

```
HMAC = HMAC-SHA256(hmac_key, HMAC_message)
```

`hmac_key` is the upper 32 bytes of the 64-byte PBKDF2 output.

### 4.3 Text encoding

The whole binary envelope is then text-encoded so it survives copy/paste:

- If `alphabet_id == 0` (base64), use `base64.urlsafe_b64encode` and strip
  padding `=`; decrypt re-pads to a multiple of 4.
- Otherwise, text-encode the whole envelope using the chosen
  `AlphabetProfile` (the same profile is used for both the inner ciphertext
  step and the outer text wrap — this is intentional and by design; it keeps
  the envelope stylistically uniform). The `alphabet_id` byte is still
  stored inside the header so decrypt can resolve it.

### 4.4 Field semantics

| Field | Size | Purpose | Notes |
|-------|------|---------|-------|
| `MAGIC` | 4B | Identify envelope | Hard-coded `b"SLNG"`. `HeaderError` if mismatch. |
| `VERSION` | 1B | Format version | `0x02` for current encrypts. `0x01` envelopes still decrypt via the v1 alphabet-id table. |
| `ITERATIONS` | 4B BE | PBKDF2 rounds | Comes from the `-s/--strength` preset or `--iterations` override. Enforced `>= MIN_ITERATIONS` on decrypt. |
| `SALT` | 16B | KDF salt | Fresh `secrets.token_bytes(16)` per encrypt. |
| `ALPHABET_ID` | 1B | Symbol profile | Must resolve via `alphabets.resolve(int)`. |
| `CIPHERTEXT` | var | Layered output | Output of `alphabet.encode(...)` as bytes. |
| `HMAC` | 32B | Authenticator | Verified first on decrypt. |

---

## 5. Public API contract

```python
def encrypt(
    plaintext: str,
    passphrase: str,
    *,
    alphabet: str = "base64",
    wordmap: dict | None = None,
    strength: str = "normal",
    iterations: int | None = None,
) -> str: ...
```

- Raises `ValueError` if `plaintext` is not a `str`, or `passphrase` is empty.
- Raises `AlphabetError` if `alphabet` is not in `alphabets.BUILTINS` (or a registered alias).
- Raises `ValueError` if `wordmap` is not bijective.
- Raises `ValueError` if `strength` is not a key of `keyderivation.STRENGTH_LEVELS`.
- Raises `ValueError` if both `strength` and `iterations` are explicitly set by the caller — they are mutually exclusive. Passing `iterations=None` (the default) means "use the `strength` preset"; passing any `int` overrides the preset.
- Raises `ValueError` if `iterations < MIN_ITERATIONS`.
- Returns a text-encoded envelope (ASCII if `alphabet == "base64"`, otherwise
  a Unicode string drawn from the symbol profile).

```python
def decrypt(
    ciphertext: str,
    passphrase: str,
    *,
    wordmap: dict | None = None,
) -> str: ...
```

- Raises `HeaderError` on malformed envelope.
- Raises `IntegrityError` on HMAC mismatch (raised **before** any layer is reversed).
- Raises `AlphabetError` if the stored `alphabet_id` is unknown to this build.
- Returns the original `str`.

Notes:

- `alphabet` is NOT a parameter on `decrypt` — the id travels inside the header.
- `wordmap` MUST match the one used at encrypt time (it is not stored in the
  envelope; it's a shared secret by convention). Mismatched wordmaps produce
  garbage plaintext but will NOT bypass HMAC — HMAC covers the pre-wordmap
  ciphertext byte stream.

---

## 6. CLI contract

Entry point: `python -m retlang ...` or installed script `retlang`.

### 6.1 Subcommands

| Subcommand | Purpose |
|------------|---------|
| `encrypt` | Encrypt stdin/file, write envelope to stdout/file. |
| `decrypt` | Decrypt envelope from stdin/file, write plaintext. |
| `genkey` | Print a fresh random passphrase (uses `secrets.token_urlsafe(32)`). No keyfiles. |
| `list-alphabets` | Print available alphabet names, one per line. |

### 6.2 Flags (shared across `encrypt` / `decrypt`)

| Flag | Meaning |
|------|---------|
| `-p, --passphrase TEXT` | Passphrase. If omitted, prompt via `getpass.getpass()` (confirms on encrypt). |
| `-i, --input FILE` | Read input from FILE. Default: stdin. |
| `-o, --output FILE` | Write output to FILE. Default: stdout. |
| `-a, --alphabet NAME` | Alphabet name (encrypt only). Default: `base64`. |
| `-s, --strength LEVEL` | PBKDF2 strength preset (encrypt only). One of `fast`, `normal`, `strong`, `paranoid`. Default: `normal`. |
| `--iterations INT` | Custom PBKDF2 iteration count (encrypt only). Mutually exclusive with `-s/--strength`; argparse enforces this via a mutually-exclusive group and exits with code `1` if both are supplied. Enforced `>= MIN_ITERATIONS`. |
| `-m, --wordmap FILE` | Path to a JSON file with a `{str: str}` mapping. Applied on both encrypt and decrypt. |

**Strength / iterations contract.**

- `-s/--strength` and `--iterations` are grouped as `argparse.add_mutually_exclusive_group()`. Supplying both is a usage error (exit code `1`).
- If neither is supplied, encrypt uses `STRENGTH_LEVELS["normal"]`.
- The chosen iteration count is written into the envelope's `ITERATIONS` header field. Decrypt never needs to be told which strength was used; it reads the field.
- `decrypt` takes neither flag — the iteration count comes from the envelope.

### 6.3 Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Generic error (bad args, I/O) |
| `2` | `IntegrityError` (tampered ciphertext / wrong passphrase) |
| `3` | `HeaderError` (not a retlang envelope / unsupported version) |
| `4` | `AlphabetError` |

### 6.4 Examples

```
# encrypt with default base64 alphabet and normal strength
$ echo "attack at dawn" | retlang encrypt -p hunter2
SLNG...  (base64url string)

# encrypt into the emoji-food alphabet
$ retlang encrypt -a emoji-food -i note.txt -o note.secret -p hunter2

# encrypt with a stronger KDF cost
$ retlang encrypt -a runes -s strong -p hunter2 "meet me at midnight"

# advanced: pin a custom iteration count (mutually exclusive with -s)
$ retlang encrypt --iterations 750000 -p hunter2 "calibrated"

# usage error: both -s and --iterations (exit code 1)
$ retlang encrypt -s strong --iterations 750000 -p hunter2 "..."

# decrypt (iteration count and alphabet are read from the envelope)
$ retlang decrypt -i note.secret -p hunter2
attack at dawn

# list available alphabets
$ retlang list-alphabets
astro
base64
emoji-animals
emoji-food
emoji-nature
emoji-smiley
geometric
letters
numbers
runes
symbols

# generate a strong passphrase
$ retlang genkey
5jK-f5F3a... (32-byte urlsafe)
```

---

## 7. Test strategy

Tests live under `tests/`, mirror the `src/retlang/` layout, and run on
stdlib `unittest`.

### 7.1 Unit tests (per layer / module)

- `tests/test_keyderivation.py`
  - Same passphrase + salt + iterations -> identical keys.
  - Different salt -> different keys.
  - `derive` rejects iterations below `MIN_ITERATIONS`.
  - `new_salt()` returns 16 bytes.
- `tests/layers/test_vigenere.py`
  - `decode(encode(x, k)) == x` for property-style random inputs.
  - Zero-length plaintext is allowed.
  - Single-byte key works.
- `tests/layers/test_wordmap.py`
  - Identity when mapping is empty.
  - Longest-key-first disambiguation (e.g. `"a"`, `"ab"` both mapped).
  - `validate` rejects non-bijective maps.
- `tests/layers/test_alphabet.py`
  - Round-trip for every built-in profile.
  - Decode of invalid symbol raises `AlphabetError`.
- `tests/test_header.py`
  - `unpack(pack(...))` is identity.
  - Bad magic -> `HeaderError`.
  - Unsupported version -> `HeaderError`.
  - Truncated buffer -> `HeaderError`.
- `tests/test_integrity.py`
  - `verify` accepts correct tag.
  - `verify` raises `IntegrityError` on single-bit flip.
  - Uses `compare_digest` (assert by monkeypatch spy or behavior test).

### 7.2 Integration (round-trip)

- `tests/test_roundtrip.py`
  - Parametrized over every built-in alphabet.
  - Parametrized over: ASCII, unicode, multi-KB, empty string plaintexts.
  - With and without wordmap.
  - Asserts `decrypt(encrypt(p, pw, alphabet=a, wordmap=w), pw, wordmap=w) == p`.

### 7.3 Tamper detection

- `tests/test_tamper.py`
  - Encrypt, then flip one bit in the base64-decoded envelope at each of:
    magic, version byte, iter bytes, salt, alphabet_id, ciphertext, hmac.
  - Every case MUST raise `IntegrityError` or `HeaderError` (never return
    plaintext).
  - Wrong passphrase MUST raise `IntegrityError` (HMAC key differs).

### 7.4 CLI

- `tests/test_cli.py`
  - Uses `subprocess` to run `python -m retlang`.
  - Round-trip via stdin/stdout.
  - `list-alphabets` output matches `alphabets.list_names()`.
  - Exit codes match §6.3.
  - `-p` omitted + stdin-is-tty path is mocked via injecting `sys.stdin`.

### 7.5 Coverage target

`>= 95%` line coverage across `src/retlang/`. CI fails below threshold.

---

## 8. Extension points

### 8.1 Adding a new alphabet

1. Add a new `AlphabetProfile` entry to `alphabets.BUILTINS` with the next
   free integer id (pick the next unused `uint8`).
2. Ensure `len(symbols)` is a supported base (64 is the default expected
   size; other sizes must be added to `layers/alphabet.py` encode/decode).
3. Add round-trip + symbol-validity tests in `tests/layers/test_alphabet.py`.
4. Bump patch version. The envelope format does NOT change — old envelopes
   keep decrypting because their `alphabet_id` is unchanged.

### 8.2 Adding a new cipher layer

1. Create `src/retlang/layers/<newlayer>.py` with matching
   `encode(data: bytes, ...) -> bytes` / `decode(data: bytes, ...) -> bytes`
   signatures.
2. Bump `VERSION` in `header.py` (add the new value to `SUPPORTED_VERSIONS`).
   Do NOT remove the old version — decrypt must branch on `header.version`
   to stay backward-compatible.
3. In `cipher.py`, gate the new layer on `version >= N`:
   - `pipeline_encrypt` always emits the newest version.
   - `pipeline_decrypt` takes a `version: int` arg and picks the matching
     inverse pipeline.
4. Document the new layer's position in §2 of this doc.
5. Add per-layer unit tests + extend `test_roundtrip.py` with a version
   parameter.

### 8.3 Swapping the KDF

Out of scope for v1. If ever required: wrap `keyderivation.derive` behind a
`KdfSpec` dataclass embedded in the header (would require a new version
byte). The existing `derive()` signature is already narrow enough to make
this a one-module change.

### 8.4 Streaming mode

Out of scope for v1. The current `integrity.tag` computes over the full
message; a streaming variant would need a chunked HMAC (encrypt-then-MAC
per chunk with a counter) and a new version byte. Layer modules are already
pure byte transforms, so they would plug in unchanged.

---

## 9. Security notes (informational, not a claim)

- HMAC is verified with `hmac.compare_digest` in `integrity.verify`. No
  other comparison path exists.
- HMAC verification happens **before** any layer is reversed. A tampered
  envelope never reaches `vigenere.decode` or `wordmap.reverse`.
- Salt is 16 bytes from `secrets.token_bytes`, fresh per encrypt.
- PBKDF2 default iterations: `200_000`; floor: `100_000`. Both are tunable
  per-envelope via the `ITERATIONS` header field, so the floor can be
  raised in future releases without breaking old envelopes (they'll decrypt
  fine; new encrypts will use the new floor).
- Passphrases are never logged and never returned from any public function.
- The `wordmap` is a convention shared out-of-band; it is NOT authenticated
  by the envelope. Treat it as stylistic layering, not as a second key.
- This is not a replacement for AES-GCM / age / libsodium. See §1.2.

---

## 10. File map summary

```
src/retlang/
├── __init__.py       # encrypt, decrypt, __version__, exceptions
├── cipher.py         # pipeline_encrypt, pipeline_decrypt
├── keyderivation.py  # derive, new_salt, resolve_strength, STRENGTH_LEVELS, DEFAULT_ITERATIONS, MIN_ITERATIONS
├── layers/
│   ├── __init__.py
│   ├── vigenere.py   # encode, decode
│   ├── wordmap.py    # apply, reverse, validate
│   └── alphabet.py   # encode, decode, AlphabetProfile
├── header.py         # pack, unpack, HeaderFields, MAGIC, SUPPORTED_VERSIONS, HEADER_SIZE
├── integrity.py      # tag, verify
├── alphabets.py      # BUILTINS (11 profiles), ALIASES, resolve, list_names
└── cli.py            # main(argv)

tests/
├── test_keyderivation.py
├── test_header.py
├── test_integrity.py
├── test_roundtrip.py
├── test_tamper.py
├── test_cli.py
└── layers/
    ├── test_vigenere.py
    ├── test_wordmap.py
    └── test_alphabet.py
```

---

## 11. Versioning

- `__version__` follows SemVer (`MAJOR.MINOR.PATCH`).
- The envelope `VERSION` byte is independent of `__version__`; it bumps only
  when the on-wire format changes.
- Rule: any change to §2 (pipeline order), §4 (envelope layout), or §5
  (public signature) requires a MAJOR bump of `__version__`. Adding an
  alphabet is PATCH. Adding an optional kwarg with a default is MINOR.
