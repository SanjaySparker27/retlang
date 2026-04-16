# retlang — Research & Design Notes

Status: partially implemented (v1)
Scope: background research, rationale, threat model, and feature planning for the `retlang` project. Historical note: the project was briefly named `secret-lang` / `secretlang` during early drafting; it is now `retlang` everywhere.
Audience: the solo maintainer, future contributors, and curious users who want to understand *what this is and what it is not* before trusting it.

---

## 0. TL;DR

`retlang` is a **toy-grade "secret language" encoder** written in pure Python 3 (stdlib only, no external dependencies). It takes plain English text and produces an encoded string built from symbols, emoji, runes, or whatever alphabet profile is chosen. It is meant to be *fun, private-between-friends, and resistant to casual eavesdropping* — nothing more.

It is **not** a replacement for AES-GCM, age, libsodium, PGP, or any real cryptographic library. If you need real crypto, use real crypto. This document exists partly to make that very clear before anyone misuses the tool.

---

## 1. Brief survey of classic ciphers

A short tour of the building blocks people historically used. Each is one or two lines — enough to justify design choices, not a full crypto textbook.

### 1.1 Caesar cipher
Shift every letter by a fixed integer `k` (e.g. `A -> D` for `k=3`).
Strength: trivial to implement, trivial to teach. Weakness: 25 possible keys in English; broken by brute force or frequency analysis in seconds.

### 1.2 Vigenère cipher
Repeat a keyword and shift each plaintext letter by the corresponding key letter. A polyalphabetic cipher — the same plaintext letter can encode to different ciphertext letters.
Strength: defeats naive frequency analysis; dramatically better than Caesar. Weakness: if key length is guessed (Kasiski examination, index of coincidence), it collapses back into parallel Caesar ciphers and falls.

### 1.3 Monoalphabetic substitution
A fixed permutation of the alphabet (`A->Q`, `B->M`, ...). 26! possible keys (~4 * 10^26).
Strength: huge keyspace, easy by hand. Weakness: preserves letter-frequency distribution; solvable by a human with a newspaper in under an hour (cryptograms as a hobby).

### 1.4 Transposition cipher
Keep the letters, rearrange their order (columnar, rail-fence, route).
Strength: destroys local structure; good in combination with substitution. Weakness: preserves letter frequencies overall; anagram-style attacks and known-plaintext attacks defeat it quickly.

### 1.5 Book cipher
Encode each word as a reference `(page, line, word)` in a shared book both parties own.
Strength: essentially a large shared codebook; very hard without the book. Weakness: entirely broken if the book is identified; cumbersome; limited vocabulary; not machine-friendly for arbitrary text.

### 1.6 One-time pad (for completeness)
XOR the message with truly random key material as long as the message, used exactly once.
Strength: information-theoretically unbreakable *if* all rules are followed. Weakness: key distribution and reuse are fatal; almost nobody gets this right in practice.

### 1.7 What we take from each
- From Vigenère: **keyed, position-dependent transformation** (but operating on bytes, not just letters).
- From substitution: **reversible per-word codewords** (dictionary layer), giving readers a "foreign language" feel rather than a letter salad.
- From book cipher: **shared-secret-as-vocabulary** intuition — the dictionary profile is part of the secret.
- From transposition: *not used directly* — adds implementation complexity for marginal strength against anyone serious, and we're being honest about threat model.
- From one-time pad: **nothing, really** — we are not pretending to be OTP-grade. PBKDF2+HMAC just gives us a usable, deterministic, auditable key schedule.

---

## 2. Why a layered approach for a "secret language"

A single classical cipher is either (a) trivially broken or (b) produces output that looks like gibberish letters. Neither fits the *feel* we want. "Secret language" means two things at once:

1. **Looks like a language**, not like `XZQ QRV FMP`. Readers should feel they're seeing runes, glyphs, emoji poetry, astro symbols — something with texture.
2. **Actually resists the casual reader** who copies the ciphertext into Google, tries rot13, and gives up.

A single layer can't do both. Either it looks structured and leaks structure, or it looks random and loses the aesthetic. So we stack:

### 2.1 The chosen pipeline (locked)
```
plaintext (UTF-8)
   |
   v
(1) PBKDF2-HMAC-SHA256 key derivation     <-- from passphrase + salt
   |
   v
(2) keyed Vigenère-style byte shift       <-- destroys raw byte patterns
   |
   v
(3) reversible dictionary word substitution   <-- gives "language" feel
   |
   v
(4) symbol / emoji alphabet encode        <-- final visual skin
   |
   v
(5) HMAC-SHA256 auth tag appended         <-- integrity + tamper detection
   |
   v
ciphertext string  (header + body + tag)
```

### 2.2 What each layer buys us
- **PBKDF2-HMAC-SHA256** turns a human passphrase into a uniformly-distributed key. It also makes brute force *slow* (configurable iterations). This is boring, standard, correct.
- **Keyed byte shift** destroys the raw byte patterns of the UTF-8 plaintext so the dictionary layer isn't substituting on visible English words. Without this layer, a dictionary substitution over literal English is just monoalphabetic-at-word-level — very weak.
- **Dictionary substitution** is what makes the output *feel like a language*. This is the aesthetic core.
- **Symbol/emoji alphabet** is the visual skin — interchangeable profiles (runes, astro, emoji, geometric) without changing the security layers underneath.
- **HMAC-SHA256 auth tag** detects tampering and catches "wrong passphrase" cleanly instead of returning garbage.

### 2.3 Why this is better than any single layer for *this* goal
- Output looks like a language, not random bytes.
- Swapping the alphabet profile (runes vs emoji vs astro) changes the *vibe* without changing the security properties.
- Even a motivated amateur can't undo it by eyeballing frequency charts — the byte-shift layer before the dictionary scrambles the statistical signal the dictionary would otherwise leak.
- HMAC means tampering is detected, not silently decoded into plausible-looking garbage.

### 2.4 Honest admission
Layering does **not** magically turn weak primitives into strong ones. The security floor is set by PBKDF2 + HMAC-SHA256 (both standard, sound primitives from `hashlib`/`hmac`). The Vigenère-style shift and dictionary layers add *obfuscation*, not *cryptographic strength*, and we should never market them as such. They make the output fun and resist casual attacks; they are not the defensive wall.

---

## 3. Threat model

A threat model is a list of who you expect to defend against and who you don't. Being precise here matters more than the algorithm choice.

### 3.1 What `retlang` aims to protect against (in-scope)
- **Casual eavesdroppers**: someone glancing at your screen, your group chat, your notebook. They see symbols and shrug.
- **Pattern guessers**: someone who assumes it's rot13, atbash, base64, or a plain substitution and tries those. The PBKDF2+shift layer defeats one-shot pattern guesses.
- **Copy-paste attackers**: someone who pastes your ciphertext into an online "decode anything" tool. Generic tools won't know our profile, header, or dictionary.
- **Tamper detection**: someone editing bytes in transit and hoping the recipient decodes something plausible. HMAC catches this and refuses to decode.
- **Wrong-passphrase detection**: silently decoding with the wrong key into garbage is bad UX and dangerous. HMAC turns this into a clean error.

### 3.2 What `retlang` does NOT protect against (out of scope)
- **Nation-state adversaries.** They have real cryptanalysts, side-channel budgets, and time. Use audited crypto.
- **Professional cryptanalysts.** Given enough ciphertext, the Vigenère-shift layer is analyzable. The dictionary substitution, given a large corpus, leaks statistical structure. These layers are for vibes, not for defense-in-depth against experts.
- **Chosen-plaintext / chosen-ciphertext attackers** with oracle access. We are not designing against adaptive attacks. Do not expose a `retlang` decoder as a public web service that returns "ok/bad tag" and expect it to survive adversarial probing.
- **Side-channel attacks** (timing, memory, power analysis). Python code running on a general-purpose OS is not constant-time. Don't rely on it.
- **Endpoint compromise.** If the attacker has your laptop, the passphrase-in-memory, the dictionary file, or the keyfile, nothing in `retlang` helps you.
- **Forward secrecy.** One leaked passphrase decrypts all past messages.
- **Deniability.** A recovered HMAC tag plus matching passphrase proves you encoded the content.
- **Legal compulsion / rubber-hose cryptanalysis.** Out of scope (and unfixable by software).

### 3.3 Plain-English summary for the README
> This is a toy-grade secret language. It keeps your messages unreadable to casual readers, lazy snoopers, and copy-paste-into-google attackers. It will not stop a determined expert, and it is absolutely not a substitute for real cryptography like age, libsodium, or a properly configured GPG. Use it for fun, notes-between-friends, and low-stakes privacy. Do not use it for anything that would hurt you if broken.

---

## 4. Feature catalogue — implement now, or defer

Each feature is rated:
- **v1** — part of the first release.
- **v1.x** — nice-to-have, add before 1.0 if time allows.
- **future** — plausible and welcome, but not blocking.

### 4.1 Passphrase mode vs keyfile mode
- **Passphrase mode (v1):** user supplies a string. We run PBKDF2-HMAC-SHA256 with a random per-message salt and a configurable iteration count (sensible default: 200_000). Salt is stored in the header. This is the default, friendliest mode.
- **Strength presets (v1, was future):** four named iteration levels — `fast` (100k, ~50 ms), `normal` (200k, ~100 ms, default), `strong` (500k, ~250 ms), `paranoid` (1M, ~500 ms). CLI flag `-s/--strength`. Advanced users can override with `--iterations INT` (mutually exclusive with the preset). The actual iteration count used is written into the envelope header so decrypt picks the right cost automatically.
- **Keyfile mode (v1.x):** user supplies a path to a file. We hash the file with SHA-256 and use the digest as the PBKDF2 input (or skip PBKDF2 if the keyfile is already high-entropy — flagged via a header bit). Useful for machine-to-machine pipelines.
- **Hybrid (future):** passphrase *and* keyfile both required. Both must be present to decode.
- **Note:** never log, echo, or persist passphrases. CLI should read passphrases via `getpass` on stdin, never as argv (argv is visible in `ps`).

### 4.2 Custom dictionary / wordmap support
- **Default dictionary (v1):** a small, curated reversible mapping of common English words -> codewords, shipped with the package.
- **User-supplied dictionary (v1):** users can pass `--dict path/to/map.json` (or `.yaml`) to override. Two-column mapping: `english_word -> codeword`. Library enforces **bijectivity** (no duplicate codewords) on load and refuses ambiguous maps.
- **Word-coverage fallback (v1):** any plaintext word not in the dictionary is passed through the byte-shift + alphabet layers only. The dictionary is *aesthetic reinforcement*, not the security primitive.
- **Multi-locale packs (future):** Spanish, Portuguese, Japanese romaji, Esperanto — community-contributed maps.

### 4.3 Alphabet / symbol profiles — v1 (now 11 profiles shipped)
Swappable visual skins applied *after* the byte-shift and dictionary layers. All profiles are bijective over the required code point range. The v1 release ships eleven built-in profiles:

- **`base64` (id 0, v1):** URL-safe base64, ASCII, compact. Default.
- **`letters` (id 1, v1):** A-Z pairs, 2 output chars per 6-bit group.
- **`numbers` (id 2, v1):** `00`-`63` pairs, 2 output chars per 6-bit group.
- **`symbols` (id 3, v1):** punctuation-only, 1 char per group, ASCII-safe.
- **`emoji-smiley` (id 4, v1):** curated face emoji. Legacy name `emoji` is an alias.
- **`emoji-animals` (id 5, v1):** curated animal emoji.
- **`emoji-food` (id 6, v1):** curated food emoji — disguises well in chat apps.
- **`emoji-nature` (id 7, v1):** curated plants, weather, landscapes.
- **`geometric` (id 8, v1):** `□ ◇ △ ▽ ◎ ● ○ ▲ ▼ ◆ ◈ ▣ ...` — portable, renders cleanly.
- **`runes` (id 9, v1):** Elder Futhark.
- **`astro` (id 10, v1):** zodiac + planetary glyphs.
- **Profile registry (v1):** profiles are declared in a single module with name, glyph array, and metadata so adding one is a ~20-line change.

**Verbosity tradeoffs.** The profiles split into three rough classes by output size. Single-char ASCII profiles (`base64`, `symbols`) are the most compact — 1 byte per 6-bit group. Pair-based ASCII profiles (`letters`, `numbers`) spend 2 output characters per 6-bit group, so output length roughly doubles; pick these only when readability in ASCII matters more than size. Emoji and glyph profiles (`emoji-*`, `geometric`, `runes`, `astro`) keep the character count the same as base64 (1 per group) but each character is multiple bytes in UTF-8, so byte size grows 2x-4x even though what the reader sees does not look longer. None of this changes security; it only changes what survives size-limited fields and how heavy the ciphertext feels.

### 4.4 Steganography — hide ciphertext in innocuous cover text (future)
Two candidate approaches:
- **Zero-width characters:** embed ciphertext as zero-width joiners / non-joiners between visible characters of a benign cover message. Very effective against visual inspection; trivially detected by any tool that renders or counts code points.
- **Word-choice stego:** given a cover template, choose synonyms whose indices encode the ciphertext bits. Much harder to detect but requires a synonym corpus.
This is **future work** — it is a significant subproject and adds a corpus dependency that fights the "stdlib only" rule unless we ship a tiny synonym table.

### 4.5 Integrity check via HMAC (v1)
HMAC-SHA256 over the full header + body, keyed with a key derived alongside the encryption key from PBKDF2 (separate info/salt label so the auth key is not identical to the shift key). Verification is constant-time (`hmac.compare_digest`). Decode refuses to return plaintext on tag mismatch.

### 4.6 Versioned header (v1)
The ciphertext begins with a compact header that includes:
- magic bytes (`SLNG` or similar)
- format version (1 byte)
- alphabet profile id (1 byte)
- dictionary id / hash (short)
- PBKDF2 iteration count (varint)
- salt (16 bytes)
- reserved flags (streaming, compressed, keyfile-mode, etc.)

This lets the format evolve without breaking old messages. Decoders either recognize the version or refuse cleanly.

### 4.7 Streaming mode for long inputs (v1.x)
For inputs > N KB, operate chunk-by-chunk so we don't hold the full plaintext in memory. Each chunk gets its own derived sub-key (from PBKDF2 output + chunk index via HKDF-style expansion using `hashlib.sha256`). A final HMAC covers the whole stream; per-chunk HMACs are optional.

### 4.8 Whitespace / punctuation preservation toggle (v1)
Two user-facing modes:
- **Preserve off (default):** everything is encoded as bytes. Output is uniform. This is the safer default — no structural leakage.
- **Preserve on:** whitespace and punctuation pass through literally, only letters/words are encoded. Output *looks* more like a language (line breaks, sentences). **Leaks structure** (word lengths, sentence boundaries). Must be documented as reducing strength.

### 4.9 CLI ergonomics (v1)
- `retlang encrypt` and `retlang decrypt`.
- Reads from stdin, writes to stdout by default; `-i` / `-o` for files.
- `--profile`, `--dict`, `--iterations`, `--preserve-structure`, `--keyfile`.
- Passphrase prompted via `getpass`; never echoed.
- Exit codes: 0 ok, 2 bad args, 3 tag mismatch (wrong passphrase or tampered), 4 unsupported format version.

### 4.10 Python library surface (v1)
Minimal, boring, typed:
```
encode(plaintext: str, *, passphrase: str, profile: str = "geometric",
       dictionary: Mapping[str, str] | None = None,
       preserve_structure: bool = False,
       iterations: int = 200_000) -> str

decode(ciphertext: str, *, passphrase: str) -> str
```
Decode reads the header and figures out profile/dictionary/version itself — callers don't need to remember settings.

### 4.11 Test corpus and golden vectors (v1)
- Round-trip tests: `decode(encode(x)) == x` over a broad fuzzed corpus including emoji, CJK, RTL scripts, control characters, empty strings, and 1-byte inputs.
- Golden vectors: pinned (passphrase, plaintext) -> ciphertext pairs so we catch accidental format drift across versions.
- Tamper tests: flipping any bit of the body must fail the HMAC check.
- Wrong-passphrase tests: must raise a clean exception, not return garbage.

### 4.12 Non-goals (explicit, so we say no fast)
- No network features.
- No key server.
- No "social" features (sharing, accounts, identity).
- No plugin system that loads arbitrary code. Dictionaries and profiles are *data*, not code.
- No external deps. Ever. `stdlib only` is a load-bearing promise.

---

## 5. Security notes and honest caveats (for the README)

A short, sharp section we should lift almost verbatim into `README.md`:

> **Read this before using `retlang` for anything real.**
>
> - This is a hobby-grade "secret language" encoder. It is designed to be fun and to resist casual readers. It is not designed to resist experts.
> - The underlying primitives (PBKDF2-HMAC-SHA256 and HMAC-SHA256) are standard and sound. The layered Vigenère-style shift and dictionary substitution are **obfuscation, not cryptography**.
> - Do not use `retlang` for medical records, legal documents, financial data, credentials, source code secrets, private keys, passwords, or anything whose disclosure would harm you or anyone else.
> - For real confidentiality, use a real tool: [age](https://github.com/FiloSottile/age), libsodium / PyNaCl, or a properly configured GPG. These are audited, peer-reviewed, and designed for the threats `retlang` explicitly declines to address.
> - Passphrase strength matters enormously. A 4-word passphrase from a large wordlist beats a short "clever" one.
> - Never paste a `retlang` passphrase into a chat box, a URL, an issue tracker, or a commit message.
> - The ciphertext format is versioned; old versions may be deprecated. We will keep decoders for old versions compatible for as long as practical, but we reserve the right to remove weak defaults.
> - There are no warranties. MIT license. Use at your own risk.

---

## 6. Open design questions (for later)

These are not blockers for v1 but are worth writing down so they aren't forgotten.

- **Dictionary provenance.** Should the default dictionary be committed verbatim, or generated deterministically from a seed? Deterministic is smaller in the repo but harder to audit at a glance.
- **Profile extensibility for non-BMP code points.** Some emoji need surrogate-pair handling on certain Python builds; pick code points that are single `ord()` values wherever possible.
- **Iteration count auto-calibration.** Should we measure at install time and pick an iteration count targeting ~100ms on the host? Convenient but adds first-run surprise.
- **Binary-safe mode.** Do we ever want to encode arbitrary bytes (not just text)? If yes, the "text in, text out" contract needs an explicit bytes variant.
- **Error messages.** Tag mismatch should say "wrong passphrase or tampered ciphertext" and nothing more. No oracles.
- **Telemetry.** None. Ever. Write it down so future contributors don't "helpfully" add it.

---

## 7. References

Deliberately limited to Python standard library documentation — no external crypto libraries, by design.

- `hashlib` — secure hashes and PBKDF2
  https://docs.python.org/3/library/hashlib.html
- `hashlib.pbkdf2_hmac` — password-based key derivation
  https://docs.python.org/3/library/hashlib.html#hashlib.pbkdf2_hmac
- `hmac` — keyed-hashing for message authentication, including `hmac.compare_digest` for constant-time comparison
  https://docs.python.org/3/library/hmac.html
- `secrets` — generating cryptographically strong random numbers (salts, nonces)
  https://docs.python.org/3/library/secrets.html
- `base64` — RFC 3548 / 4648 encodings, useful for the ASCII-safe profile and header framing
  https://docs.python.org/3/library/base64.html
- `getpass` — reading passphrases from the terminal without echoing
  https://docs.python.org/3/library/getpass.html
- `argparse` — CLI argument parsing
  https://docs.python.org/3/library/argparse.html
- `unicodedata` — useful for normalizing plaintext before encoding (NFC) so round-trips are stable
  https://docs.python.org/3/library/unicodedata.html
- `json` — dictionary / profile file format
  https://docs.python.org/3/library/json.html

Background reading (not code deps, just context for the design choices):
- RFC 2898 / RFC 8018 — PKCS #5, PBKDF2 specification.
- RFC 2104 — HMAC.
- NIST SP 800-132 — recommendations for password-based key derivation.
- Kahn, *The Codebreakers* — historical context for classical ciphers.

---

## 8. Decision log

One-liners, dated, so future-me remembers *why*.

- **Stdlib only.** Non-negotiable. Keeps install trivial, reduces supply-chain surface, makes the codebase teachable.
- **No network features.** Scope creep killer. If a user wants to send a message, they copy-paste.
- **Layered pipeline is locked.** PBKDF2 -> Vigenère-shift -> dictionary -> alphabet -> HMAC. Order chosen so that: key material is high-entropy before use; byte patterns are destroyed before word-level substitution; the aesthetic skin is last so it can be swapped without touching security layers; HMAC covers everything.
- **HMAC is mandatory, not optional.** An encrypt-without-auth mode is a footgun and we won't ship it.
- **Default profile is geometric, not emoji.** Emoji rendering varies across platforms; geometric glyphs are more portable for the "works everywhere" default. Emoji is one command-line flag away.
- **Solo maintainer, MIT.** No CLA, no bureaucracy. Contributions welcome; scope is guarded.
