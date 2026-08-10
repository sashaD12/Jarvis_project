import json
import os
import re
import time
import urllib.parse
import urllib.request
from typing import Any

from config_loader import BASE_DIR

CACHE_FILE = os.path.join(BASE_DIR, "name_resolve_cache.json")
CACHE_TTL_SEC = 60 * 60 * 24 * 30
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)

UK_TO_LAT = {
    "а": "a", "б": "b", "в": "v", "г": "h", "ґ": "g", "д": "d", "е": "e", "є": "ye",
    "ж": "zh", "з": "z", "и": "y", "і": "i", "ї": "yi", "й": "i", "к": "k", "л": "l",
    "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch", "ю": "yu",
    "я": "ya", "ь": "", "ъ": "", "ы": "y", "э": "e",
}


def _load_cache() -> dict[str, Any]:
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_cache(cache: dict[str, Any]) -> None:
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _http_get_json(url: str, timeout: float = 8.0) -> dict[str, Any] | list[Any] | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
        data = json.loads(raw)
        if isinstance(data, (dict, list)):
            return data
    except Exception:
        return None
    return None


def _http_get_text(url: str, timeout: float = 8.0) -> str:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _normalize_key(text: str) -> str:
    text = text.lower().strip()
    text = text.replace("ё", "е")
    text = re.sub(r"[^\w\sа-яіїєґ0-9]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def _to_latin(text: str) -> str:
    return "".join(UK_TO_LAT.get(ch, ch) for ch in text.lower())


def _query_search_variants(query: str) -> list[str]:
    q = _normalize_key(query)
    if not q:
        return []

    variants = [q]
    latin = _to_latin(q)
    variants.append(latin)
    variants.append(re.sub(r"\s+", "", q))
    variants.append(re.sub(r"\s+", "", latin))

    digits = re.findall(r"\d+", q)
    letters = re.sub(r"\d+", " ", latin)
    letters = re.sub(r"\s+", " ", letters).strip()
    if letters and digits:
        variants.append(f"{letters}{digits[0]}")
        variants.append(f"{letters} {digits[0]}")

    if re.fullmatch(r"[a-zа-яіїєґ]+", q) and len(q) >= 4:
        stem = _to_latin(q[:-1]) if q[-1] in "ауеоиіїюяьйу" else latin
        if stem:
            variants.append(stem)

    uniq: list[str] = []
    seen: set[str] = set()
    for item in variants:
        item = item.strip()
        if item and item not in seen:
            seen.add(item)
            uniq.append(item)
    return uniq


def steam_store_candidates(query: str, limit: int = 5) -> list[str]:
    names: list[str] = []
    variants = _query_search_variants(query)

    for term in variants:
        url = f"https://steamcommunity.com/actions/SearchApps/{urllib.parse.quote(term)}"
        data = _http_get_json(url)
        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name") or "").strip()
                if name and name not in names:
                    names.append(name)
                if len(names) >= limit:
                    return names

    for term in variants:
        for lang in ("english", "ukrainian", "russian"):
            url = (
                "https://store.steampowered.com/api/storesearch/"
                f"?term={urllib.parse.quote(term)}&l={lang}&cc=US"
            )
            data = _http_get_json(url)
            if not isinstance(data, dict):
                continue
            items = data.get("items") or []
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name") or "").strip()
                if name and name not in names:
                    names.append(name)
                if len(names) >= limit:
                    return names
    return names


def duckduckgo_candidates(query: str, limit: int = 5) -> list[str]:
    names: list[str] = []
    for term in _query_search_variants(query)[:4]:
        for suffix in ("game", "игра", "гра steam"):
            q = f"{term} {suffix}"
            html = _http_get_text(
                "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": q})
            )
            for match in re.finditer(
                r"(?:uddg=([^&\"]+)|store\.steampowered\.com/app/\d+/([^/?\"']+))",
                html,
            ):
                link = ""
                slug = ""
                if match.group(1):
                    try:
                        link = urllib.parse.unquote(match.group(1))
                    except Exception:
                        link = ""
                if match.group(2):
                    slug = match.group(2).replace("_", " ").strip()
                if "store.steampowered.com/app/" in link:
                    slug = link.rstrip("/").split("/")[-1].replace("_", " ")
                    slug = re.sub(r"\s+", " ", slug).strip()
                if slug and slug not in names and len(slug) > 2:
                    names.append(slug)
                if len(names) >= limit:
                    return names

            url = "https://api.duckduckgo.com/?" + urllib.parse.urlencode(
                {"q": q, "format": "json", "no_html": 1, "skip_disambig": 1}
            )
            data = _http_get_json(url)
            if isinstance(data, dict):
                heading = str(data.get("Heading") or "").strip()
                if heading and heading not in names:
                    names.append(heading)
        if len(names) >= limit:
            break
    return names[:limit]


def resolve_informal_names(query: str, limit: int = 6) -> list[str]:
    key = _normalize_key(query)
    if not key:
        return []

    cache = _load_cache()
    entry = cache.get(key)
    if isinstance(entry, dict):
        created = float(entry.get("created_at", 0))
        names = entry.get("names")
        if isinstance(names, list) and time.time() - created < CACHE_TTL_SEC:
            return [str(n) for n in names if str(n).strip()][:limit]

    names: list[str] = []
    for source in (steam_store_candidates, duckduckgo_candidates):
        try:
            for name in source(query, limit=limit):
                if name and name not in names:
                    names.append(name)
        except Exception:
            continue
        if len(names) >= limit:
            break

    if names:
        long_names = [n for n in names if len(n.split()) >= 2]
        for long_name in long_names[:2]:
            try:
                for extra in steam_store_candidates(long_name, limit=3):
                    if extra not in names:
                        names.append(extra)
            except Exception:
                pass

    cache[key] = {"created_at": time.time(), "names": names[:limit], "query": query}
    _save_cache(cache)
    return names[:limit]
