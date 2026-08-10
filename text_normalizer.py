import re
from typing import Iterable

PHRASE_REPLACEMENTS: list[tuple[str, str]] = [
    (r"\bсвіткриф\b", "відкрий"),
    (r"\bсвіткрий\b", "відкрий"),
    (r"\bвідкриф\b", "відкрий"),
    (r"\bоткрый\b", "відкрий"),
    (r"\bоткрой\b", "відкрий"),
    (r"\bвідкрити\b", "відкрий"),
    (r"\bзапустив\b", "запусти"),
    (r"\bзапустіть\b", "запусти"),
    (r"\bзапустить\b", "запусти"),
    (r"\bзапуск\b", "запусти"),
    (r"\bвипустити\b", "запустити"),
    (r"\bвключив\b", "включи"),
    (r"\bпокажи\b", "покажи"),
    (r"\bхоче\b", "хочу"),
    (r"\bвклющу\b", "включи"),
    (r"\bвключиш\b", "включи"),
    (r"\bвключити\b", "включи"),
    (r"\bувімкни\b", "включи"),
    (r"\bввімкни\b", "включи"),
    (r"\bінтерставру\b", "інстаграм"),
    (r"\bінтерстаграм\b", "інстаграм"),
    (r"\bінстаграму\b", "інстаграм"),
    (r"\bінстаграмі\b", "інстаграм"),
    (r"\bспотіфаю\b", "spotify"),
    (r"\bспотіфай\b", "spotify"),
    (r"\bпоїжджати\b", "пограти"),
    (r"\bпоїждати\b", "пограти"),
    (r"\bпоїрати\b", "пограти"),
    (r"\bпоіграти\b", "пограти"),
    (r"\bпоїграти\b", "пограти"),
    (r"\bпограть\b", "пограти"),
    (r"\bправит\b", "пограти"),
    (r"\bігруть\b", "грати"),
    (r"\bіграти\b", "грати"),
    (r"\bтанкі\b", "танки"),
    (r"\bтанці\b", "танки"),
    (r"\bштанки\b", "танки"),
    (r"\bдавай\s+в\s+([а-яa-zіїєґ0-9]+)\s+і\s+грати\b", r"давай пограти в \1"),
    (r"\bдавай\s+в\s+([а-яa-zіїєґ0-9]+)\s+ігруть\b", r"давай пограти в \1"),
    (r"\bдавай\s+в\s+([а-яa-zіїєґ0-9]+)\s+грати\b", r"давай пограти в \1"),
    (r"\bстол\s*зон\b", "stalcraft"),
    (r"\bстал\s*зон\b", "stalcraft"),
    (r"\bстолзон\b", "stalcraft"),
    (r"\bсталзон\b", "stalcraft"),
    (r"\bсталкрафт\b", "stalcraft"),
    (r"\bstal\s*craft\b", "stalcraft"),
    (r"\bепік\s*геймс\b", "епік геймс"),
    (r"\bепик\s*геймс\b", "епік геймс"),
    (r"\bepic\s*games\b", "епік геймс"),
]

DEFAULT_WAKE_ALIASES = [
    "атос",
    "ата з",
    "а тас",
    "атас",
    "атась",
    "ата",
    "пас",
    "паса",
    "паси",
    "ніда",
    "нада",
    "ataus",
    "atas",
    "a tas",
    "ata s",
    "pass",
    "pas",
]

COMMAND_VERBS = (
    "запусти",
    "відкрий",
    "включи",
    "покажи",
    "вимкни",
)

COMMAND_STEMS = (
    "включ",
    "запуск",
    "запуст",
    "відкр",
    "откры",
    "показ",
    "вимкн",
    "погра",
    "хочу",
    "давай",
)


def collapse_spaced_phrase(text: str, phrase: str) -> str:
    compact = re.sub(r"\s+", "", phrase.lower())
    if not compact:
        return text
    pattern = r"\s*".join(re.escape(ch) for ch in compact)
    return re.sub(pattern, phrase.lower(), text, flags=re.IGNORECASE)


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i]
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            curr.append(min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[-1]


def compact_text(text: str) -> str:
    return re.sub(r"\s+", "", text.lower())


def latin_to_cyr_approx(text: str) -> str:
    table = str.maketrans(
        {
            "a": "а", "e": "е", "i": "і", "o": "о", "u": "у", "y": "и",
            "b": "б", "c": "с", "d": "д", "g": "г", "h": "х", "k": "к",
            "l": "л", "m": "м", "n": "н", "p": "п", "r": "р", "s": "с",
            "t": "т", "v": "в", "w": "в", "x": "кс", "z": "з",
        }
    )
    return text.lower().translate(table)


def basic_cleanup(text: str) -> str:
    normalized = text.lower().strip()
    normalized = normalized.replace("ё", "е")
    normalized = re.sub(r"[^\w\sа-яіїєґ']+", " ", normalized, flags=re.UNICODE)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def apply_phrase_replacements(text: str) -> str:
    result = text
    for pattern, replacement in PHRASE_REPLACEMENTS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", result).strip()


def apply_wake_word_fuzzy(text: str, wake_word: str, candidates: Iterable[str]) -> str:
    lowered = text.lower().strip()
    if wake_word and re.search(rf"(?<!\w){re.escape(wake_word)}(?!\w)", lowered):
        return lowered

    cand_list = sorted({c for c in candidates if c}, key=len, reverse=True)
    for cand in cand_list:
        pattern = rf"(?<!\w){re.escape(cand)}(?!\w)"
        if re.search(pattern, lowered):
            return re.sub(pattern, wake_word, lowered, count=1)

    tokens = lowered.split()
    if not tokens:
        return lowered

    wake_compact = compact_text(wake_word)
    max_dist = 2 if len(wake_compact) <= 5 else 1
    candidate_compacts = [compact_text(c) for c in cand_list]
    if wake_compact not in candidate_compacts:
        candidate_compacts.insert(0, wake_compact)

    best: tuple[int, int] | None = None
    for n in range(1, min(4, len(tokens) + 1)):
        joined = "".join(tokens[:n])
        prefix = compact_text(joined)
        prefix_lat = compact_text(latin_to_cyr_approx(joined))
        for target in candidate_compacts:
            for variant in (prefix, prefix_lat):
                if not variant:
                    continue
                dist = levenshtein(variant, target)
                if dist <= max_dist:
                    if best is None or dist < best[0] or (dist == best[0] and n < best[1]):
                        best = (dist, n)

    if best is not None:
        first = tokens[0]
        if any(first.startswith(stem) for stem in COMMAND_STEMS):
            return lowered
        rest = " ".join(tokens[best[1]:])
        return f"{wake_word} {rest}".strip()

    return lowered


def strip_wake_prefix(text: str, wake_word: str) -> str:
    if not text.startswith(wake_word):
        return text
    rest = text[len(wake_word):].strip()
    rest = re.sub(r"^[а-яa-zієїґ]\s+", "", rest, flags=re.IGNORECASE)
    return rest.strip()


def inject_wake_if_command(text: str, wake_word: str) -> str:
    if not text or not wake_word:
        return text
    if text == wake_word or text.startswith(wake_word + " "):
        return text
    first = text.split(" ", 1)[0]
    if first in COMMAND_VERBS or any(first.startswith(stem) for stem in COMMAND_STEMS):
        return f"{wake_word} {text}".strip()
    return text


def normalize_recognized_text(
    text: str,
    wake_word: str,
    aliases: list[str] | None = None,
) -> str:
    normalized = basic_cleanup(text)
    if not normalized:
        return ""

    candidates = [wake_word] + list(aliases or []) + DEFAULT_WAKE_ALIASES
    unique_candidates: list[str] = []
    seen: set[str] = set()
    for cand in candidates:
        key = cand.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        unique_candidates.append(key)

    unique_candidates.sort(key=len, reverse=True)
    for cand in unique_candidates:
        normalized = collapse_spaced_phrase(normalized, cand)

    normalized = apply_phrase_replacements(normalized)
    normalized = apply_wake_word_fuzzy(normalized, wake_word, unique_candidates)
    normalized = apply_phrase_replacements(normalized)
    normalized = inject_wake_if_command(normalized, wake_word)
    return re.sub(r"\s+", " ", normalized).strip()
