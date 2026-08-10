import re
from typing import Any

import numpy as np

from config_loader import load_commands, load_settings

_MODEL = None
_MODEL_NAME = ""
_PHRASE_CACHE: dict[str, np.ndarray] = {}
_APP_CACHE: dict[str, np.ndarray] = {}
_INTENT_CACHE: dict[str, np.ndarray] = {}
_INTENT_ROWS: list[dict[str, Any]] | None = None


def invalidate_intent_cache() -> None:
    global _INTENT_ROWS
    _INTENT_ROWS = None


def _neural_settings() -> dict[str, Any]:
    settings = load_settings()
    neural = settings.get("neural")
    if not isinstance(neural, dict):
        neural = {}
    return {
        "enabled": bool(neural.get("enabled", True)),
        "model": str(
            neural.get(
                "model",
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            )
        ),
        "text_threshold": float(neural.get("text_threshold", 0.48)),
        "program_threshold": float(neural.get("program_threshold", 0.38)),
        "intent_threshold": float(neural.get("intent_threshold", 0.48)),
        "intent_first": bool(neural.get("intent_first", True)),
    }


def _get_model():
    global _MODEL, _MODEL_NAME
    cfg = _neural_settings()
    if not cfg["enabled"]:
        return None
    model_name = cfg["model"]
    if _MODEL is not None and _MODEL_NAME == model_name:
        return _MODEL
    try:
        from fastembed import TextEmbedding
    except ImportError as e:
        raise ImportError(
            "Пакет fastembed не встановлено. Виконайте: pip install fastembed"
        ) from e

    print(f"Loading neural parser model '{model_name}'...")
    _MODEL = TextEmbedding(model_name=model_name)
    _MODEL_NAME = model_name
    return _MODEL


def _embed_texts(texts: list[str]) -> np.ndarray:
    model = _get_model()
    if model is None or not texts:
        return np.zeros((0, 1), dtype=np.float32)
    vectors = list(model.embed(texts))
    arr = np.asarray(vectors, dtype=np.float32)
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return arr / norms


def _cosine_sim(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    if matrix.size == 0:
        return np.zeros((0,), dtype=np.float32)
    return matrix @ query_vec


def _build_command_phrases() -> list[str]:
    settings = load_settings()
    commands = load_commands().get("commands", [])
    wake = str(settings.get("wake_word", "атас"))
    phrases = {
        wake,
        f"{wake} котра година",
        f"{wake} покажи погоду",
        f"{wake} відкрий браузер",
        f"{wake} відкрий ютуб",
        f"{wake} включи музику",
        f"{wake} вимкни комп'ютер",
    }
    for cmd in commands:
        action = str(cmd.get("action", ""))
        for keyword in cmd.get("keywords", []):
            phrases.add(f"{wake} {keyword}")
            if action == "open_program":
                phrases.add(f"{wake} {keyword} програму")
    return sorted(phrases)


def _get_phrase_matrix(phrases: list[str]) -> np.ndarray:
    missing = [p for p in phrases if p not in _PHRASE_CACHE]
    if missing:
        embedded = _embed_texts(missing)
        for text, vec in zip(missing, embedded):
            _PHRASE_CACHE[text] = vec
    if not phrases:
        return np.zeros((0, 1), dtype=np.float32)
    return np.stack([_PHRASE_CACHE[p] for p in phrases], axis=0)


def _get_app_matrix(apps: list[dict[str, str]]) -> tuple[list[str], np.ndarray]:
    names = [str(a.get("name", "")).strip() for a in apps if str(a.get("name", "")).strip()]
    missing = [n for n in names if n not in _APP_CACHE]
    if missing:
        embedded = _embed_texts(missing)
        for text, vec in zip(missing, embedded):
            _APP_CACHE[text] = vec
    if not names:
        return [], np.zeros((0, 1), dtype=np.float32)
    matrix = np.stack([_APP_CACHE[n] for n in names], axis=0)
    return names, matrix


def _clean_slot(value: str) -> str:
    cleaned = value.strip(" .,!?;:\"'`")
    cleaned = re.sub(
        r"^(?:будь\s+ласка|мені|нам|давай|зараз|швидко|просто)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"\s+(?:будь\s+ласка|пожалуйста|please)$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def extract_program_slot(text: str) -> str | None:
    known_games = {
        "танки",
        "циву",
        "цива",
        "хойку",
        "хой4",
        "hoi4",
        "stalcraft",
        "столзон",
    }
    patterns = [
        r"(?:запусти|відкрий|ввімкни|увімкни)\s+(?:мені\s+|нам\s+|будь\s+ласка\s+)*(?:програму\s+|додаток\s+|гру\s+)?(.+)$",
        r"(?:хочу|давай|можна|треба|потрібно|прошу)\s+(?:мені\s+)?(?:запустити|відкрити|ввімкнути|пограти\s+в|грати\s+в|пограти|відкрити)\s+(.+)$",
        r"(?:хочу|давай|можна|треба|прошу)\s+(?:\S+\s+){0,3}?в\s+(.+)$",
        r"давай\s+в\s+(.+)$",
        r"(?:пограти|пограєм|пограємо|грати|граємо|ігруть)\s+(?:в\s+)?(.+)$",
        r"(?:запустимо|відкриємо)\s+(.+)$",
        r"\bв\s+(танки|циву|цива|хойку|хой\s*4|stalcraft|столзон)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            value = _clean_slot(match.group(1))
            value = re.sub(
                r"^(?:програму|додаток|гру|application|game)\s+",
                "",
                value,
                flags=re.IGNORECASE,
            ).strip()
            value = re.sub(
                r"\s+(?:і|и|та)\s+(?:грати|ігруть|пограти).*$",
                "",
                value,
                flags=re.IGNORECASE,
            ).strip()
            parts = value.split()
            if parts:
                last = parts[-1].lower().replace(" ", "")
                if last in known_games:
                    value = parts[-1]
            if value and value.lower() not in {
                "програму",
                "програма",
                "додаток",
                "гру",
                "гра",
                "браузер",
                "ютуб",
                "youtube",
                "інтернет",
                "ключи",
                "ключі",
                "погоду",
                "погода",
                "час",
            }:
                return value
    return None


def extract_song_slot(text: str) -> str | None:
    patterns = [
        r"(?:включи|постав|пограй|увімкни|ввімкни|знайди|послухай)\s+(?:мені\s+|нам\s+)?(?:музику|пісню|трек|пісеньку)\s+(?:з|із|от|від)\s+(.+)$",
        r"(?:включи|постав|пограй|увімкни|ввімкни|знайди|послухай)\s+(?:мені\s+|нам\s+)?(?:музику|пісню|трек|пісеньку)\s+(.+)$",
        r"(?:включи|постав|пограй|увімкни|ввімкни|знайди)\s+(?:мені\s+)?(.+)$",
        r"(?:хочу\s+послухати|давай\s+послухаємо)\s+(.+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            value = _clean_slot(match.group(1) or "")
            if value.lower() in {"музику", "пісню", "трек", "пісеньку", "music"}:
                return None
            return value or None
    return None


def _build_intent_rows() -> list[dict[str, Any]]:
    global _INTENT_ROWS
    if _INTENT_ROWS is not None:
        return _INTENT_ROWS
    rows: list[dict[str, Any]] = []
    for cmd in load_commands().get("commands", []):
        cmd_id = str(cmd.get("id", ""))
        action = str(cmd.get("action", ""))
        priority = int(cmd.get("priority", 0))
        params = cmd.get("params", {}) if isinstance(cmd.get("params"), dict) else {}
        examples = [str(x).strip() for x in cmd.get("examples", []) if str(x).strip()]
        if not examples:
            examples = [str(k).strip() for k in cmd.get("keywords", []) if str(k).strip()]
        for example in examples:
            rows.append(
                {
                    "example": example.lower(),
                    "command": cmd_id,
                    "action": action,
                    "priority": priority,
                    "params": params,
                }
            )
    _INTENT_ROWS = rows
    return rows


def _get_intent_matrix(rows: list[dict[str, Any]]) -> np.ndarray:
    examples = [str(r["example"]) for r in rows]
    missing = [e for e in examples if e not in _INTENT_CACHE]
    if missing:
        embedded = _embed_texts(missing)
        for text, vec in zip(missing, embedded):
            _INTENT_CACHE[text] = vec
    if not examples:
        return np.zeros((0, 1), dtype=np.float32)
    return np.stack([_INTENT_CACHE[e] for e in examples], axis=0)


_REJECT_EXAMPLES = [
    "привіт",
    "вітаю",
    "добрий день",
    "як справи",
    "що робиш",
    "дякую",
    "ок",
    "добре",
    "нічого",
    "просто тест",
    "розкажи щось",
    "що ти вмієш",
]


def neural_find_commands(text: str) -> list[dict[str, Any]]:
    cfg = _neural_settings()
    if not cfg["enabled"] or not text.strip():
        return []
    try:
        utterance = text.strip().lower()
        wake = str(load_settings().get("wake_word", "атас")).lower()
        if utterance.startswith(wake):
            utterance = utterance[len(wake):].strip()
        utterance = re.sub(r"^[а-яa-zієїґ]\s+", "", utterance, flags=re.IGNORECASE).strip()
        if not utterance:
            return []

        rows = _build_intent_rows()
        if not rows:
            return []
        matrix = _get_intent_matrix(rows)
        query = _embed_texts([utterance])[0]
        sims = _cosine_sim(query, matrix)
        if sims.size == 0:
            return []

        reject_matrix = _get_phrase_matrix(_REJECT_EXAMPLES)
        reject_sims = _cosine_sim(query, reject_matrix)
        best_reject = float(np.max(reject_sims)) if reject_sims.size else 0.0

        best_by_command: dict[str, dict[str, Any]] = {}
        for idx, score in enumerate(sims.tolist()):
            row = rows[idx]
            cmd_id = str(row["command"])
            current = best_by_command.get(cmd_id)
            if current is None or float(score) > float(current["score"]):
                best_by_command[cmd_id] = {
                    "command": cmd_id,
                    "action": row["action"],
                    "params": row["params"],
                    "priority": row["priority"],
                    "score": float(score),
                    "example": row["example"],
                }

        if not best_by_command:
            return []

        ranked = sorted(best_by_command.values(), key=lambda item: item["score"], reverse=True)
        best_score = float(ranked[0]["score"])
        threshold = max(cfg["intent_threshold"], 0.62)
        if best_score < threshold or best_reject >= best_score - 0.03:
            print(
                f"Neural command check: '{utterance}' -> none "
                f"(best={best_score:.3f}, reject={best_reject:.3f})"
            )
            return []

        program = extract_program_slot(utterance)
        song = extract_song_slot(utterance)
        launch_hint = bool(
            re.search(
                r"\b(?:запусти|відкрий|пограти|грати|ігруть|пограєм|запустимо|відкриємо|давай\s+в|хочу\s+.+\s+в)\b",
                utterance,
                flags=re.IGNORECASE,
            )
        ) or bool(program)

        if program and launch_hint:
            open_cand = best_by_command.get("open_program")
            score = float(open_cand["score"]) if open_cand else max(best_score, 0.7)
            result = [
                {
                    "command": "open_program",
                    "action": "open_program",
                    "params": (open_cand or {}).get("params", {}),
                    "priority": int((open_cand or {}).get("priority", 3)),
                    "keyword": f"neural:{(open_cand or {}).get('example', 'запусти програму')}",
                    "delay": 0,
                    "song": None,
                    "program": program,
                    "confidence": round(score, 3),
                    "source": "neural",
                }
            ]
            print(f"Neural command check: '{utterance}' -> open_program({result[0]['confidence']}) program='{program}'")
            return result

        present: list[dict[str, Any]] = []
        for item in ranked:
            score = float(item["score"])
            action = str(item["action"])
            if score < threshold:
                continue
            if present and score < 0.85:
                continue
            if score < best_score - 0.05 and score < 0.88:
                continue

            cmd_song = song if action == "youtube_search" else None
            if action == "open_program":
                continue

            present.append(
                {
                    "command": item["command"],
                    "action": action,
                    "params": item["params"],
                    "priority": int(item["priority"]),
                    "keyword": f"neural:{item['example']}",
                    "delay": 0,
                    "song": cmd_song,
                    "program": None,
                    "confidence": round(score, 3),
                    "source": "neural",
                }
            )
            if len(present) == 1 and best_score < 0.85:
                break

        present.sort(key=lambda item: (-float(item["confidence"]), -float(item["priority"])))
        if present:
            names = ", ".join(
                f"{item['command']}({item['confidence']})" for item in present
            )
            print(f"Neural command check: '{utterance}' -> {names}")
        else:
            print(f"Neural command check: '{utterance}' -> none")
        return present
    except Exception as e:
        print(f"Neural command check skipped: {e}")
        return []


def neural_detect_intent(text: str) -> dict[str, Any] | None:
    found = neural_find_commands(text)
    if not found:
        return None
    return found[0]


def neural_refine_text(text: str) -> str:
    cfg = _neural_settings()
    if not cfg["enabled"] or not text.strip():
        return text
    try:
        program_match = re.search(
            r"\b(?:запусти|відкрий)\s+(.+)$",
            text.strip(),
            flags=re.IGNORECASE,
        )
        if program_match:
            program_name = program_match.group(1).strip()
            refined_program = neural_best_program_name(program_name)
            if refined_program and refined_program.lower() != program_name.lower():
                wake = load_settings().get("wake_word", "атас")
                verb = "запусти" if "запусти" in text.lower() else "відкрий"
                result = f"{wake} {verb} {refined_program}"
                print(f"Neural text refine: '{text}' -> '{result}'")
                return result
            return text

        if cfg["intent_first"]:
            return text

        phrases = _build_command_phrases()
        q = _embed_texts([text])[0]
        matrix = _get_phrase_matrix(phrases)
        sims = _cosine_sim(q, matrix)
        if sims.size == 0:
            return text
        best_idx = int(np.argmax(sims))
        best_score = float(sims[best_idx])
        best_phrase = phrases[best_idx]
        if best_score >= cfg["text_threshold"]:
            if best_phrase != text:
                print(f"Neural text refine: '{text}' -> '{best_phrase}' ({best_score:.3f})")
            return best_phrase
    except Exception as e:
        print(f"Neural text refine skipped: {e}")
    return text


def neural_best_program_name(query: str) -> str | None:
    ranked = neural_rank_programs(query, limit=5)
    if not ranked:
        return None
    try:
        from slang_parser import acronym_score
    except Exception:
        top = ranked[0]
        if float(top.get("similarity") or 0.0) >= 0.78:
            return top["name"]
        return None

    best_name = None
    best_value = -1.0
    for item in ranked:
        name = str(item.get("name") or "")
        sim = float(item.get("similarity") or 0.0)
        acro = acronym_score(query, name) / 100.0
        if acro < 0.45 and sim < 0.78:
            continue
        if acro < 0.2:
            continue
        combined = (sim * 0.4) + (acro * 0.6)
        if combined > best_value:
            best_value = combined
            best_name = name
    return best_name


def neural_rank_programs(
    query: str,
    apps: list[dict[str, str]] | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    cfg = _neural_settings()
    if not cfg["enabled"] or not query.strip():
        return []
    try:
        if apps is None:
            from program_finder import load_app_index

            apps = load_app_index()
        names, matrix = _get_app_matrix(apps)
        if not names:
            return []
        q = _embed_texts([query])[0]
        sims = _cosine_sim(q, matrix)
        order = np.argsort(-sims)
        try:
            from slang_parser import acronym_score
        except Exception:
            acronym_score = None

        results: list[dict[str, Any]] = []
        seen: set[str] = set()
        for idx in order:
            score = float(sims[int(idx)])
            if score < cfg["program_threshold"]:
                break
            name = names[int(idx)]
            app = next((a for a in apps if a.get("name") == name), None)
            if app is None:
                continue
            acro = float(acronym_score(query, name)) if acronym_score else 0.0
            if acro < 20.0 and score < 0.72:
                continue
            if acro < 15.0:
                continue
            key = f"{app.get('path')}::{name}".lower()
            if key in seen:
                continue
            seen.add(key)
            combined = (score * 40.0) + (acro * 0.6)
            results.append(
                {
                    "name": name,
                    "path": app.get("path"),
                    "source": f"neural:{app.get('source', 'unknown')}",
                    "score": round(combined, 2),
                    "similarity": score,
                    "acronym": acro,
                }
            )
            if len(results) >= limit * 3:
                break
        results.sort(key=lambda item: (-float(item["score"]), -float(item["similarity"])))
        return results[:limit]
    except Exception as e:
        print(f"Neural program rank skipped: {e}")
        return []


def warmup_neural_parser() -> None:
    cfg = _neural_settings()
    if not cfg["enabled"]:
        return
    _get_model()
    _ = _embed_texts(["атас запусти програму", "яка зараз погода"])
    _ = _build_intent_rows()
    _ = _get_intent_matrix(_build_intent_rows())
