"""Named 64-symbol alphabet profiles.

Each profile defines exactly 64 unique symbols. We use them to encode
binary data, 6 bits per symbol. The default profile is url-safe base64.

Supported profiles (id in header byte):
    0  base64         url-safe base64 (A-Z a-z 0-9 - _)
    1  letters        64 unique 2-letter digraphs (A-Z only, output len *2)
    2  numbers        64 unique 2-digit codes "00".."63" (output len *2)
    3  symbols        64 unique ASCII + Unicode punctuation/symbols
    4  emoji-smiley   64 unique smiley emoji (U+1F600 range)
    5  emoji-animals  64 unique animal emoji
    6  emoji-food     64 unique food/drink emoji
    7  emoji-nature   64 unique plant/weather/nature emoji
    8  geometric      64 geometric unicode shapes
    9  runes          64 runic-style unicode glyphs
   10  astro          mix of astrological / zodiac / planetary symbols

Note on symbols of length > 1 (letters, numbers): the outer alphabet
encoder expects each "symbol" to uniquely map to a 6-bit group, but it
concatenates symbols without separators. Multi-character digit/letter
digraphs are fine as long as NO symbol in the set is a prefix of any
other -- our letter/number profiles use fixed-width 2-char codes so
every slice of length 2 is unambiguous.

NOTE on VERSION bump: the alphabet_id byte in the envelope header
changed when we moved from 5 profiles to 11. The header VERSION byte
was bumped from 1 to 2 so that parsers can distinguish old ciphertexts
from new ones. See src/retlang/header.py.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

# ------------------------------------------------------------------
# Alphabet definitions
# ------------------------------------------------------------------

_BASE64_URLSAFE: str = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789-_"
)


def _letters_digraphs() -> List[str]:
    """Return 64 unique 2-letter digraphs of A-Z.

    We walk AA, AB, AC ... alphabetically and take the first 64 pairs.
    AA..AZ = 26, BA..BZ = 26, CA..CL = 12 -> total 64.
    """
    out: List[str] = []
    alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for first in alpha:
        for second in alpha:
            out.append(first + second)
            if len(out) == 64:
                return out
    return out


def _number_codes() -> List[str]:
    """Return ["00", "01", ..., "63"] -- 64 unique two-digit codes."""
    return [f"{i:02d}" for i in range(64)]


# 64 unique ASCII / Unicode punctuation and symbol chars.
# No letters, digits, or whitespace. Each is a single codepoint.
_SYMBOLS: List[str] = [
    # ASCII punctuation (32 chars). '=' is intentionally excluded because
    # it is reserved as the alphabet-encoder pad symbol in
    # layers/alphabet.py.
    "!", '"', "#", "$", "%", "&", "'", "(", ")", "*",
    "+", ",", "-", ".", "/", ":", ";", "<", ">", "?",
    "@", "[", "\\", "]", "^", "`", "{", "|",
    "}", "~", "_", "\u00A1",  # ¡
    # Unicode punctuation / symbols (32 more to reach 64).
    "\u00BF",  # ¿
    "\u00AB",  # «
    "\u00BB",  # »
    "\u00A7",  # §
    "\u00B6",  # ¶
    "\u2020",  # †
    "\u2021",  # ‡
    "\u2022",  # •
    "\u2026",  # …
    "\u2030",  # ‰
    "\u2032",  # ′
    "\u2033",  # ″
    "\u2039",  # ‹
    "\u203A",  # ›
    "\u00A2",  # ¢
    "\u00A3",  # £
    "\u00A4",  # ¤
    "\u00A5",  # ¥
    "\u20AC",  # €
    "\u20B9",  # ₹
    "\u00A6",  # ¦
    "\u00A9",  # ©
    "\u00AE",  # ®
    "\u2122",  # ™
    "\u00B0",  # °
    "\u00B1",  # ±
    "\u00D7",  # ×
    "\u00F7",  # ÷
    "\u2248",  # ≈
    "\u2260",  # ≠
    "\u221E",  # ∞
    "\u2264",  # ≤
]


# 64 smiley emoji glyphs from the U+1F600 range (bijective-friendly).
_EMOJI_SMILEY: List[str] = [
    "\U0001F600", "\U0001F601", "\U0001F602", "\U0001F603", "\U0001F604",
    "\U0001F605", "\U0001F606", "\U0001F609", "\U0001F60A", "\U0001F60B",
    "\U0001F60D", "\U0001F60E", "\U0001F60F", "\U0001F610", "\U0001F611",
    "\U0001F612", "\U0001F613", "\U0001F614", "\U0001F615", "\U0001F616",
    "\U0001F617", "\U0001F618", "\U0001F619", "\U0001F61A", "\U0001F61B",
    "\U0001F61C", "\U0001F61D", "\U0001F61E", "\U0001F61F", "\U0001F620",
    "\U0001F621", "\U0001F622", "\U0001F623", "\U0001F624", "\U0001F625",
    "\U0001F626", "\U0001F627", "\U0001F628", "\U0001F629", "\U0001F62A",
    "\U0001F62B", "\U0001F62C", "\U0001F62D", "\U0001F62E", "\U0001F62F",
    "\U0001F630", "\U0001F631", "\U0001F632", "\U0001F633", "\U0001F634",
    "\U0001F635", "\U0001F636", "\U0001F637", "\U0001F638", "\U0001F639",
    "\U0001F63A", "\U0001F63B", "\U0001F63C", "\U0001F63D", "\U0001F63E",
    "\U0001F63F", "\U0001F640", "\U0001F641", "\U0001F642",
]


# 64 animal emoji -- pulled from U+1F400..U+1F43F plus a few supplementary
# animal codepoints to reach exactly 64 unique glyphs.
_EMOJI_ANIMALS: List[str] = [
    # U+1F400..U+1F43F (64 contiguous codepoints is already 64, perfect)
    "\U0001F400", "\U0001F401", "\U0001F402", "\U0001F403", "\U0001F404",
    "\U0001F405", "\U0001F406", "\U0001F407", "\U0001F408", "\U0001F409",
    "\U0001F40A", "\U0001F40B", "\U0001F40C", "\U0001F40D", "\U0001F40E",
    "\U0001F40F", "\U0001F410", "\U0001F411", "\U0001F412", "\U0001F413",
    "\U0001F414", "\U0001F415", "\U0001F416", "\U0001F417", "\U0001F418",
    "\U0001F419", "\U0001F41A", "\U0001F41B", "\U0001F41C", "\U0001F41D",
    "\U0001F41E", "\U0001F41F", "\U0001F420", "\U0001F421", "\U0001F422",
    "\U0001F423", "\U0001F424", "\U0001F425", "\U0001F426", "\U0001F427",
    "\U0001F428", "\U0001F429", "\U0001F42A", "\U0001F42B", "\U0001F42C",
    "\U0001F42D", "\U0001F42E", "\U0001F42F", "\U0001F430", "\U0001F431",
    "\U0001F432", "\U0001F433", "\U0001F434", "\U0001F435", "\U0001F436",
    "\U0001F437", "\U0001F438", "\U0001F439", "\U0001F43A", "\U0001F43B",
    "\U0001F43C", "\U0001F43D", "\U0001F43E", "\U0001F43F",
]


# 64 food/drink emoji -- drawn from U+1F32D..U+1F37F plus supplementary.
_EMOJI_FOOD: List[str] = [
    # U+1F32D..U+1F37F (83 codepoints). Take first 64.
    "\U0001F32D", "\U0001F32E", "\U0001F32F", "\U0001F330", "\U0001F331",
    "\U0001F332", "\U0001F333", "\U0001F334", "\U0001F335", "\U0001F336",
    "\U0001F337", "\U0001F338", "\U0001F339", "\U0001F33A", "\U0001F33B",
    "\U0001F33C", "\U0001F33D", "\U0001F33E", "\U0001F33F", "\U0001F340",
    "\U0001F341", "\U0001F342", "\U0001F343", "\U0001F344", "\U0001F345",
    "\U0001F346", "\U0001F347", "\U0001F348", "\U0001F349", "\U0001F34A",
    "\U0001F34B", "\U0001F34C", "\U0001F34D", "\U0001F34E", "\U0001F34F",
    "\U0001F350", "\U0001F351", "\U0001F352", "\U0001F353", "\U0001F354",
    "\U0001F355", "\U0001F356", "\U0001F357", "\U0001F358", "\U0001F359",
    "\U0001F35A", "\U0001F35B", "\U0001F35C", "\U0001F35D", "\U0001F35E",
    "\U0001F35F", "\U0001F360", "\U0001F361", "\U0001F362", "\U0001F363",
    "\U0001F364", "\U0001F365", "\U0001F366", "\U0001F367", "\U0001F368",
    "\U0001F369", "\U0001F36A", "\U0001F36B", "\U0001F36C",
]


# 64 nature emoji -- trees, flowers, weather, stars, etc.
# Drawn from mixed ranges. Verified unique.
_EMOJI_NATURE: List[str] = [
    # trees / plants / leaves
    "\U0001F333",  # deciduous tree
    "\U0001F334",  # palm tree
    "\U0001F335",  # cactus
    "\U0001F332",  # evergreen tree
    "\U0001F331",  # seedling
    "\U0001F340",  # four leaf clover
    "\U0001F341",  # maple leaf
    "\U0001F342",  # fallen leaf
    "\U0001F343",  # leaf fluttering in wind
    "\U0001F33E",  # sheaf of rice / wheat
    "\U0001F33F",  # herb
    "\U0001F344",  # mushroom
    # flowers
    "\U0001F337",  # tulip
    "\U0001F338",  # cherry blossom
    "\U0001F339",  # rose
    "\U0001F33A",  # hibiscus
    "\U0001F33B",  # sunflower
    "\U0001F33C",  # blossom
    "\U0001F33D",  # ear of corn
    "\U0001F490",  # bouquet
    # weather / sky
    "\u2600",       # sun
    "\u2601",       # cloud
    "\u2602",       # umbrella
    "\u2603",       # snowman
    "\u2604",       # comet
    "\u26C4",       # snowman without snow
    "\u26C5",       # sun behind cloud
    "\u26C8",       # thunder cloud and rain
    "\u26A1",       # high voltage / lightning
    "\U0001F324",   # white sun with small cloud
    "\U0001F325",   # white sun behind cloud
    "\U0001F326",   # white sun behind cloud with rain
    "\U0001F327",   # cloud with rain
    "\U0001F328",   # cloud with snow
    "\U0001F329",   # cloud with lightning
    "\U0001F32A",   # cloud with tornado
    "\U0001F32B",   # fog
    "\U0001F32C",   # wind blowing face
    # celestial
    "\u2B50",       # star
    "\U0001F31F",   # glowing star
    "\U0001F320",   # shooting star
    "\U0001F31E",   # sun with face
    "\U0001F31D",   # full moon with face
    "\U0001F31A",   # new moon with face
    "\U0001F311",   # new moon
    "\U0001F312",   # waxing crescent moon
    "\U0001F313",   # first quarter moon
    "\U0001F314",   # waxing gibbous moon
    "\U0001F315",   # full moon
    "\U0001F316",   # waning gibbous moon
    "\U0001F317",   # last quarter moon
    "\U0001F318",   # waning crescent moon
    "\U0001F319",   # crescent moon
    "\U0001F30D",   # earth globe europe-africa
    "\U0001F30E",   # earth globe americas
    "\U0001F30F",   # earth globe asia-australia
    # landscapes / water / fire
    "\U0001F30B",   # volcano
    "\U0001F30A",   # water wave
    "\U0001F300",   # cyclone
    "\U0001F308",   # rainbow
    "\U0001F525",   # fire
    "\U0001F4A7",   # droplet
    "\U0001F4A6",   # sweat droplets
    "\u2744",       # snowflake
]


# 64 geometric unicode shapes from the Geometric Shapes block (U+25A0..U+25FF).
_GEOMETRIC: List[str] = [
    "\u25A0", "\u25A1", "\u25A2", "\u25A3", "\u25A4", "\u25A5", "\u25A6", "\u25A7",
    "\u25A8", "\u25A9", "\u25AA", "\u25AB", "\u25AC", "\u25AD", "\u25AE", "\u25AF",
    "\u25B0", "\u25B1", "\u25B2", "\u25B3", "\u25B4", "\u25B5", "\u25B6", "\u25B7",
    "\u25B8", "\u25B9", "\u25BA", "\u25BB", "\u25BC", "\u25BD", "\u25BE", "\u25BF",
    "\u25C0", "\u25C1", "\u25C2", "\u25C3", "\u25C4", "\u25C5", "\u25C6", "\u25C7",
    "\u25C8", "\u25C9", "\u25CA", "\u25CB", "\u25CC", "\u25CD", "\u25CE", "\u25CF",
    "\u25D0", "\u25D1", "\u25D2", "\u25D3", "\u25D4", "\u25D5", "\u25D6", "\u25D7",
    "\u25D8", "\u25D9", "\u25DA", "\u25DB", "\u25DC", "\u25DD", "\u25DE", "\u25DF",
]

# 64 runic-style unicode glyphs from the Runic block (U+16A0..U+16F8).
_RUNES: List[str] = [
    "\u16A0", "\u16A1", "\u16A2", "\u16A3", "\u16A4", "\u16A5", "\u16A6", "\u16A7",
    "\u16A8", "\u16A9", "\u16AA", "\u16AB", "\u16AC", "\u16AD", "\u16AE", "\u16AF",
    "\u16B0", "\u16B1", "\u16B2", "\u16B3", "\u16B4", "\u16B5", "\u16B6", "\u16B7",
    "\u16B8", "\u16B9", "\u16BA", "\u16BB", "\u16BC", "\u16BD", "\u16BE", "\u16BF",
    "\u16C0", "\u16C1", "\u16C2", "\u16C3", "\u16C4", "\u16C5", "\u16C6", "\u16C7",
    "\u16C8", "\u16C9", "\u16CA", "\u16CB", "\u16CC", "\u16CD", "\u16CE", "\u16CF",
    "\u16D0", "\u16D1", "\u16D2", "\u16D3", "\u16D4", "\u16D5", "\u16D6", "\u16D7",
    "\u16D8", "\u16D9", "\u16DA", "\u16DB", "\u16DC", "\u16DD", "\u16DE", "\u16DF",
]

# 64 astro/zodiac/planetary symbols.
_ASTRO: List[str] = [
    # 12 zodiac signs (U+2648..U+2653)
    "\u2648", "\u2649", "\u264A", "\u264B", "\u264C", "\u264D",
    "\u264E", "\u264F", "\u2650", "\u2651", "\u2652", "\u2653",
    # planets and bodies
    "\u2609",  # sun
    "\u263D",  # moon first quarter
    "\u263E",  # moon last quarter
    "\u263F",  # mercury
    "\u2640",  # venus / female
    "\u2641",  # earth
    "\u2642",  # mars / male
    "\u2643",  # jupiter
    "\u2644",  # saturn
    "\u2645",  # uranus
    "\u2646",  # neptune
    "\u2647",  # pluto
    # aspects / misc astrological
    "\u260A",  # ascending node
    "\u260B",  # descending node
    "\u260C",  # conjunction
    "\u260D",  # opposition
    "\u260E",  # black telephone - filler symbol, distinct
    "\u260F",  # white telephone
    "\u2610",  # ballot box
    "\u2611",  # ballot box with check
    "\u2612",  # ballot box with x
    "\u2613",  # saltire
    "\u2614",  # umbrella with rain
    "\u2615",  # hot beverage
    "\u2616",  # white shogi piece
    "\u2617",  # black shogi piece
    "\u2618",  # shamrock
    "\u2619",  # reversed rotated floral heart
    "\u261A",  # back of envelope
    "\u261B",  # black right pointing index
    "\u261C",  # white left pointing index
    "\u261D",  # white up pointing index
    "\u261E",  # white right pointing index
    "\u261F",  # white down pointing index
    "\u2620",  # skull and crossbones
    "\u2621",  # caution sign
    "\u2622",  # radioactive
    "\u2623",  # biohazard
    "\u2624",  # caduceus
    "\u2625",  # ankh
    "\u2626",  # orthodox cross
    "\u2627",  # chi rho
    "\u2628",  # cross of lorraine
    "\u2629",  # cross of jerusalem
    "\u262A",  # star and crescent
    "\u262B",  # farsi symbol
    "\u262C",  # adi shakti
    "\u262D",  # hammer and sickle
    "\u262E",  # peace symbol
    "\u262F",  # yin yang
    "\u2630",  # trigram for heaven
    "\u2638",  # wheel of dharma
]


# ------------------------------------------------------------------
# Profile descriptor: each profile carries its symbol tuple plus a
# fixed `width` (chars per 6-bit group). width > 1 means every symbol
# MUST have exactly `width` characters (checked below).
# ------------------------------------------------------------------

class AlphabetProfile:
    """Immutable record describing a 64-symbol alphabet profile."""

    __slots__ = ("name", "symbols", "width")

    def __init__(self, name: str, symbols: Tuple[str, ...], width: int) -> None:
        if len(symbols) != 64:
            raise ValueError(
                f"alphabet '{name}' must have exactly 64 symbols, got {len(symbols)}"
            )
        if len(set(symbols)) != 64:
            raise ValueError(f"alphabet '{name}' contains duplicate symbols")
        if width < 1:
            raise ValueError(f"alphabet '{name}' width must be >= 1")
        for sym in symbols:
            if not isinstance(sym, str) or len(sym) == 0:
                raise ValueError(
                    f"alphabet '{name}' symbol must be non-empty str"
                )
            if width > 1 and len(sym) != width:
                raise ValueError(
                    f"alphabet '{name}' symbol {sym!r} must be {width} chars"
                )
        self.name = name
        self.symbols = symbols
        self.width = width

    def __iter__(self):
        return iter(self.symbols)

    def __len__(self) -> int:
        return len(self.symbols)

    def __getitem__(self, idx: int) -> str:
        return self.symbols[idx]


def _mk(name: str, raw: List[str], width: int = 1) -> AlphabetProfile:
    return AlphabetProfile(name, tuple(raw), width)


# Registry: stable mapping of canonical profile name -> profile.
ALPHABETS: Dict[str, AlphabetProfile] = {
    "base64":        _mk("base64",        list(_BASE64_URLSAFE), 1),
    "letters":       _mk("letters",       _letters_digraphs(),   2),
    "numbers":       _mk("numbers",       _number_codes(),       2),
    "symbols":       _mk("symbols",       _SYMBOLS,              1),
    "emoji-smiley":  _mk("emoji-smiley",  _EMOJI_SMILEY,         1),
    "emoji-animals": _mk("emoji-animals", _EMOJI_ANIMALS,        1),
    "emoji-food":    _mk("emoji-food",    _EMOJI_FOOD,           1),
    "emoji-nature":  _mk("emoji-nature",  _EMOJI_NATURE,         1),
    "geometric":     _mk("geometric",     _GEOMETRIC,            1),
    "runes":         _mk("runes",         _RUNES,                1),
    "astro":         _mk("astro",         _ASTRO,                1),
}

# Numeric ids stored in envelope header. IDs 0..10.
NAME_TO_ID: Dict[str, int] = {
    "base64":        0,
    "letters":       1,
    "numbers":       2,
    "symbols":       3,
    "emoji-smiley":  4,
    "emoji-animals": 5,
    "emoji-food":    6,
    "emoji-nature":  7,
    "geometric":     8,
    "runes":         9,
    "astro":        10,
}

# Backwards-compat alias: the old "emoji" profile is now "emoji-smiley".
# Lookups under "emoji" still resolve, but the canonical name emitted on
# list/preview is "emoji-smiley".
_ALIASES: Dict[str, str] = {
    "emoji": "emoji-smiley",
}

ID_TO_NAME: Dict[int, str] = {v: k for k, v in NAME_TO_ID.items()}

# Legacy alias kept so existing callers using ALPHABET_IDS still work.
ALPHABET_IDS: Dict[str, int] = dict(NAME_TO_ID)


def _canonical(name: str) -> str:
    if name in ALPHABETS:
        return name
    if name in _ALIASES:
        return _ALIASES[name]
    raise ValueError(
        f"unknown alphabet '{name}'. Known: {list_alphabets()}"
    )


def list_alphabets() -> List[str]:
    """Return the canonical profile names in their stable id order."""
    # Order by id so CLI output is deterministic and human-sensible.
    return [ID_TO_NAME[i] for i in sorted(ID_TO_NAME)]


def alphabet_symbols(name: str) -> Tuple[str, ...]:
    """Return the 64-symbol tuple for a named alphabet."""
    canon = _canonical(name)
    return ALPHABETS[canon].symbols


def alphabet_profile(name: str) -> AlphabetProfile:
    """Return the full profile object for a named alphabet."""
    canon = _canonical(name)
    return ALPHABETS[canon]


def alphabet_id(name: str) -> int:
    """Return the numeric id for a named alphabet (alias-aware)."""
    canon = _canonical(name)
    return NAME_TO_ID[canon]


def name_from_id(alphabet_id_value: int) -> str:
    try:
        return ID_TO_NAME[alphabet_id_value]
    except KeyError as exc:
        raise ValueError(f"unknown alphabet id {alphabet_id_value}") from exc


def alphabet_preview(name: str, n: int = 16) -> str:
    """Return the first n symbols of the named alphabet joined as a string.

    Used by the CLI `list-alphabets` subcommand to show a recognizable
    preview per profile.
    """
    if n < 0:
        raise ValueError("n must be >= 0")
    profile = alphabet_profile(name)
    n = min(n, len(profile))
    # Join with a thin space so multi-char codes (letters / numbers) are
    # visually separated in CLI output.
    joiner = " " if profile.width > 1 else ""
    return joiner.join(profile.symbols[:n])
