import re
from typing import Iterable

UK_TO_LAT_VARIANTS = [
    {
        "а": "a", "б": "b", "в": "v", "г": "h", "ґ": "g", "д": "d", "е": "e", "є": "ye",
        "ж": "zh", "з": "z", "и": "y", "і": "i", "ї": "yi", "й": "i", "к": "k", "л": "l",
        "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
        "ф": "f", "х": "h", "ц": "c", "ч": "ch", "ш": "sh", "щ": "shch", "ю": "yu",
        "я": "ya", "ь": "", "ъ": "", "ы": "y", "э": "e",
    },
    {
        "а": "a", "б": "b", "в": "v", "г": "h", "ґ": "g", "д": "d", "е": "e", "є": "ye",
        "ж": "zh", "з": "z", "и": "i", "і": "i", "ї": "yi", "й": "i", "к": "k", "л": "l",
        "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
        "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch", "ю": "yu",
        "я": "ya", "ь": "", "ъ": "", "ы": "y", "э": "e",
    },
]

ROMAN_TO_DIGIT = {
    "i": "1",
    "ii": "2",
    "iii": "3",
    "iv": "4",
    "v": "5",
    "vi": "6",
    "vii": "7",
    "viii": "8",
    "ix": "9",
    "x": "10",
}

STOP_WORDS = {
    "the", "a", "and", "edition", "game", "complete", "deluxe", "ultimate", "hd",
    "sid", "meier", "meiers", "sids",
}


def to_latin_forms(text: str) -> list[str]:
    forms: list[str] = []
    for table in UK_TO_LAT_VARIANTS:
        forms.append("".join(table.get(ch, ch) for ch in text.lower()))
    uniq: list[str] = []
    for form in forms:
        if form not in uniq:
            uniq.append(form)
    return uniq


def to_latin(text: str) -> str:
    return to_latin_forms(text)[0]


def normalize(text: str) -> str:
    text = text.lower().strip().replace("ё", "е")
    text = re.sub(r"[^\w\sа-яіїєґ0-9]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def compact(text: str) -> str:
    return re.sub(r"\s+", "", normalize(text))


def _compact_key(text: str) -> str:
    return re.sub(r"\s+", "", text.lower())


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


def app_acronyms(app_name: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", to_latin(app_name))
    significant = [t for t in tokens if t not in STOP_WORDS]
    if not significant:
        return set()

    parts: list[str] = []
    for token in significant:
        if token in ROMAN_TO_DIGIT:
            parts.append(ROMAN_TO_DIGIT[token])
        elif token.isdigit():
            parts.append(token)
        else:
            parts.append(token[0])

    keys = {"".join(parts)}
    letters = "".join(p for p in parts if p.isalpha())
    digits = "".join(p for p in parts if p.isdigit())
    if letters:
        keys.add(letters)
    if letters and digits:
        keys.add(letters + digits)
        keys.add(f"{letters} {digits}")

    keys.add(compact(app_name))
    for form in to_latin_forms(app_name):
        keys.add(compact(form))
        if "civilization" in form.replace(" ", ""):
            keys.update({"civ", "civilization", "civa", "civu"})

    return {k for k in keys if len(_compact_key(k)) >= 3}


def query_codes(query: str) -> set[str]:
    q = normalize(query)
    codes = {q, compact(q)}

    for latin in to_latin_forms(q):
        codes.add(latin)
        codes.add(compact(latin))
        digits = re.findall(r"\d+", latin)
        letters = re.sub(r"\d+", "", latin)
        letters = re.sub(r"\s+", "", letters)
        if letters:
            codes.add(letters)
            if digits:
                codes.add(letters + digits[0])
                codes.add(f"{letters} {digits[0]}")

        compact_latin = compact(latin)
        if len(compact_latin) >= 4 and compact_latin[-1] in "aeiouy":
            stem = compact_latin[:-1]
            if len(stem) >= 3:
                codes.add(stem)
        if len(compact_latin) >= 5:
            codes.add(compact_latin[:4])

    return {c for c in codes if len(_compact_key(c)) >= 3}


def acronym_score(query: str, app_name: str) -> float:
    q_codes = query_codes(query)
    a_codes = app_acronyms(app_name)
    if not q_codes or not a_codes:
        return 0.0

    name_compact = compact(to_latin(app_name))
    best = 0.0
    for qc in q_codes:
        qn = _compact_key(qc)
        if len(qn) < 3:
            continue

        if qn in name_compact and len(qn) >= 3:
            if name_compact.startswith(qn) or f" {qn}" in f" {name_compact}":
                best = max(best, 96.0)
            elif len(qn) >= 4:
                best = max(best, 90.0)

        for ac in a_codes:
            an = _compact_key(ac)
            if len(an) < 3:
                continue
            if qn == an:
                best = max(best, 100.0)
            elif len(qn) >= 4 and len(an) >= 4 and (qn in an or an in qn):
                best = max(best, 92.0)
            else:
                dist = levenshtein(qn, an)
                if dist <= 1 and min(len(qn), len(an)) >= 4:
                    best = max(best, 88.0)
                elif dist <= 2 and min(len(qn), len(an)) >= 5:
                    best = max(best, 82.0)
    return best


def best_acronym_matches(
    query: str,
    apps: Iterable[dict],
    min_score: float = 88.0,
) -> list[tuple[float, dict]]:
    scored: list[tuple[float, dict]] = []
    for app in apps:
        score = acronym_score(query, str(app.get("name", "")))
        if score >= min_score:
            scored.append((score, app))
    scored.sort(key=lambda item: (-item[0], len(str(item[1].get("name", "")))))
    return scored
