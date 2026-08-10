import json
import os
import re
from collections import deque
from typing import Any

import requests

from config_loader import load_commands, load_settings

_VALID_ACTIONS = {
    "open_url",
    "youtube_search",
    "show_time",
    "weather",
    "shutdown",
    "open_program",
}

_RECENT_UTTERANCES: deque[str] = deque(maxlen=3)
_LAST_LLM_COMMANDS: list[dict[str, Any]] = []

_CHITCHAT_EXACT = {
    "привіт",
    "здрастуй",
    "здрастуйте",
    "добрий день",
    "доброго ранку",
    "добрий вечір",
    "як справи",
    "дякую",
    "спасибі",
    "супер",
    "ок",
    "окей",
    "ага",
    "угу",
}

_CLARIFY_PATTERNS = (
    "ще раз",
    "ту саму",
    "те саме",
    "ту ж",
    "повтор",
    "знову",
    "теж саме",
)


def clear_llm_context() -> None:
    _RECENT_UTTERANCES.clear()
    _LAST_LLM_COMMANDS.clear()


def _is_chitchat(text: str) -> bool:
    cleaned = " ".join(text.lower().strip().split())
    if cleaned in _CHITCHAT_EXACT:
        return True
    if cleaned.startswith("привіт") and len(cleaned.split()) <= 4:
        return True
    if cleaned.startswith("як справи"):
        return True
    return False


def _is_clarification(text: str) -> bool:
    cleaned = " ".join(text.lower().strip().split())
    if not cleaned:
        return False
    return any(pattern in cleaned for pattern in _CLARIFY_PATTERNS)


_DEFAULT_INTENTS: dict[str, str] = {
    "open_browser": "Відкрити браузер / інтернет / Chrome.",
    "youtube": "Відкрити YouTube без пошуку пісні.",
    "play_music": "Увімкнути або знайти музику/пісню.",
    "time": "Сказати котра година.",
    "weather": "Сказати погоду / температуру / прогноз.",
    "shutdown": "Вимкнути комп'ютер.",
    "open_program": "Запустити гру або програму на комп'ютері.",
}


def _llm_settings() -> dict[str, Any]:
    settings = load_settings()
    llm = settings.get("llm")
    if not isinstance(llm, dict):
        llm = {}
    base_url = str(
        os.environ.get("LLM_BASE_URL")
        or llm.get("base_url")
        or "http://127.0.0.1:11434"
    ).rstrip("/")
    model = str(os.environ.get("LLM_MODEL") or llm.get("model") or "llama3.2").strip()
    return {
        "enabled": bool(llm.get("enabled", True)),
        "provider": str(llm.get("provider", "ollama")).strip().lower(),
        "base_url": base_url,
        "model": model,
        "timeout_sec": float(llm.get("timeout_sec", 25)),
        "prefer_over_keywords": bool(llm.get("prefer_over_keywords", True)),
        "temperature": float(llm.get("temperature", 0.1)),
        "use_context": bool(llm.get("use_context", True)),
    }


def llm_available() -> bool:
    cfg = _llm_settings()
    if not cfg["enabled"]:
        return False
    try:
        if cfg["provider"] in {"ollama"}:
            url = f"{cfg['base_url']}/api/tags"
            resp = requests.get(url, timeout=2)
            return resp.status_code == 200
        url = f"{cfg['base_url']}/v1/models"
        if cfg["base_url"].endswith("/v1"):
            url = f"{cfg['base_url']}/models"
        resp = requests.get(url, timeout=2)
        return resp.status_code == 200
    except Exception:
        return False


def _chat_url(cfg: dict[str, Any]) -> str:
    base = cfg["base_url"]
    if cfg["provider"] == "openai_compat":
        if base.endswith("/v1"):
            return f"{base}/chat/completions"
        return f"{base}/v1/chat/completions"
    if base.endswith("/v1"):
        return f"{base}/chat/completions"
    return f"{base}/v1/chat/completions"


def _known_program_hints() -> list[str]:
    programs = load_commands().get("programs", {})
    hints = sorted({str(k) for k in programs.keys()})
    hints.extend(
        [
            "танки",
            "world of tanks",
            "циву",
            "цива",
            "civilization",
            "хойку",
            "hoi4",
            "hearts of iron",
            "stalcraft",
            "discord",
            "steam",
            "epic",
            "telegram",
            "spotify",
        ]
    )
    unique: list[str] = []
    seen: set[str] = set()
    for item in hints:
        key = item.lower().strip()
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(key)
    return unique[:40]


def _build_system_prompt(commands: list[dict[str, Any]]) -> str:
    catalog: list[dict[str, Any]] = []
    for cmd in commands:
        cmd_id = str(cmd.get("id") or "")
        catalog.append(
            {
                "id": cmd_id,
                "intent": str(cmd.get("intent") or _DEFAULT_INTENTS.get(cmd_id, "")),
                "action": cmd.get("action"),
                "keywords": cmd.get("keywords", [])[:6],
                "examples": cmd.get("examples", [])[:8],
            }
        )
    recent = list(_RECENT_UTTERANCES)
    recent_block = ""
    if recent:
        recent_block = (
            "Останні фрази користувача (контекст діалогу):\n"
            + "\n".join(f"- {item}" for item in recent)
            + "\n"
        )
    programs = ", ".join(_known_program_hints())
    examples = (
        "Приклади (учись по сенсу):\n"
        "- можеш запустити танки -> open_program program=танки\n"
        "- хочу пограти в циву -> open_program program=цива\n"
        "- ввімкни музику з інстаграму / інтерставру -> play_music song=інстаграм\n"
        "- постав щось спокійне -> play_music\n"
        "- відкрий ютуб -> youtube\n"
        "- як на вулиці / чи буде дощ -> weather\n"
        "- котра година -> time\n"
        "- відкрий хром -> open_browser\n"
        "- привіт / як справи / дякую -> commands=[]\n"
    )
    rules = (
        "Правила вибору:\n"
        "1) Спочатку визнач намір поточної фрази, потім підбери id з каталогу.\n"
        "2) Попередній контекст враховуй ЛИШЕ якщо фраза — уточнення "
        "(ще раз / ту саму / іншу / теж). Інакше ігноруй минулі фрази.\n"
        "3) Запуск гри/додатку (пограти, відкрий гру, запусти...) — open_program, "
        "НЕ browser і НЕ youtube.\n"
        "4) Музика/пісня/трек/плейлист/увімкни щось з X (інстаграм, спотіфай) — "
        "play_music; song = джерело/назва. Це НЕ open_program.\n"
        "5) Просто відкрити сайт YouTube — youtube; шукати трек — play_music.\n"
        "6) Погода/температура/дощ/вулиця — weather.\n"
        "7) Час/година — time.\n"
        "8) Вимкнути ПК — shutdown.\n"
        "9) Браузер/інтернет/хром — open_browser. "
        "Слова про інтернет без відкрий/зайди НЕ означають браузер.\n"
        "10) Вітання, подяка, балачка без дії — commands=[].\n"
        "11) Якщо сумніваєшся між дією і балачкою — commands=[] і confidence<0.5.\n"
        "12) Максимум 2 команди. id лише з каталогу.\n"
        "13) Для open_program обов'язково program (танки, цива, discord...).\n"
        "14) confidence 0..1 — впевненість у намірі.\n"
    )
    return (
        "Ти — семантичний парсер намірів голосового асистента Jarvis.\n"
        "Завдання: зрозуміти ЗА ЗМІСТОМ, яку команду хоче користувач, "
        "навіть якщо Whisper сильно спотворив слова.\n"
        "Не чіпляйся лише до точних ключових слів — відновлюй сенс по синонімах "
        "і типових помилках ASR.\n"
        "Відповідай ЛИШЕ JSON:\n"
        '{"commands":[{"id":"open_program","program":"танки","song":null,'
        '"confidence":0.86,"reason":"хоче запустити гру"}]}\n'
        f"{rules}"
        f"{examples}"
        f"Відомі програми/ігри: {programs}\n"
        f"{recent_block}"
        f"Каталог команд:\n{json.dumps(catalog, ensure_ascii=False)}"
    )


def _extract_json(text: str) -> dict[str, Any] | None:
    raw = text.strip()
    if not raw:
        return None
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _map_llm_commands(
    payload: dict[str, Any],
    command_by_id: dict[str, dict[str, Any]],
    text: str = "",
) -> list[dict[str, Any]]:
    items = payload.get("commands")
    if not isinstance(items, list):
        return []
    result: list[dict[str, Any]] = []
    for item in items[:2]:
        if not isinstance(item, dict):
            continue
        cmd_id = str(item.get("id") or "").strip()
        cmd_def = command_by_id.get(cmd_id)
        if cmd_def is None:
            continue
        action = str(cmd_def.get("action") or "")
        if action not in _VALID_ACTIONS:
            continue
        program = item.get("program")
        song = item.get("song")
        program_value = str(program).strip() if program else None
        song_value = str(song).strip() if song else None
        if action == "open_program" and not program_value:
            try:
                from neural_parser import extract_program_slot

                program_value = extract_program_slot(text)
            except Exception:
                program_value = None
            if not program_value:
                continue
        if action != "open_program":
            program_value = None
        if action != "youtube_search":
            song_value = None
        if action == "youtube_search" and not song_value:
            try:
                from neural_parser import extract_song_slot

                song_value = extract_song_slot(text)
            except Exception:
                song_value = None
        confidence_raw = item.get("confidence")
        try:
            confidence = float(confidence_raw) if confidence_raw is not None else 0.85
        except (TypeError, ValueError):
            confidence = 0.85
        confidence = max(0.0, min(1.0, confidence))
        if confidence < 0.55:
            continue
        reason = str(item.get("reason") or "").strip()
        reason_l = reason.lower()
        if any(
            token in reason_l
            for token in ("балачка", "вітання", "подяка", "без дії", "chitchat")
        ):
            continue
        result.append(
            {
                "command": cmd_id,
                "action": action,
                "params": cmd_def.get("params", {}),
                "priority": int(cmd_def.get("priority", 0)),
                "keyword": "llm",
                "delay": 0,
                "song": song_value or None,
                "program": program_value or None,
                "confidence": round(confidence, 3),
                "reason": reason or None,
                "source": "llm",
            }
        )
    return result


def _log_mapped(utterance: str, mapped: list[dict[str, Any]]) -> None:
    if mapped:
        names = ", ".join(
            f"{item['command']}"
            + (f":{item['program']}" if item.get("program") else "")
            + (f":{item['song']}" if item.get("song") else "")
            + (f"({item.get('confidence')})" if item.get("confidence") is not None else "")
            for item in mapped
        )
        reasons = "; ".join(
            str(item.get("reason")) for item in mapped if item.get("reason")
        )
        extra = f" | reason: {reasons}" if reasons else ""
        print(f"Local LLM: '{utterance}' -> {names}{extra}")
    else:
        print(f"Local LLM: '{utterance}' -> none")


def llm_parse_commands(text: str) -> list[dict[str, Any]]:
    global _LAST_LLM_COMMANDS
    cfg = _llm_settings()
    if not cfg["enabled"] or not text.strip():
        return []
    utterance = text.strip()
    if _is_chitchat(utterance):
        if cfg["use_context"]:
            _RECENT_UTTERANCES.append(utterance)
        print(f"Local LLM: '{utterance}' -> none (chitchat)")
        return []
    if cfg["use_context"] and _is_clarification(utterance) and _LAST_LLM_COMMANDS:
        repeated = [dict(item) for item in _LAST_LLM_COMMANDS]
        for item in repeated:
            item["keyword"] = "llm-context"
            item["reason"] = "уточнення: повтор попередньої команди"
        _RECENT_UTTERANCES.append(utterance)
        _log_mapped(utterance, repeated)
        return repeated
    commands_data = load_commands()
    commands = commands_data.get("commands", [])
    command_by_id = {str(c["id"]): c for c in commands}
    user_content = utterance
    if cfg["use_context"] and _RECENT_UTTERANCES:
        user_content = (
            "Попередній контекст:\n"
            + "\n".join(f"- {item}" for item in _RECENT_UTTERANCES)
            + f"\n\nПоточна фраза: {utterance}\n"
            "Визнач намір саме поточної фрази. "
            "Контекст враховуй тільки якщо це уточнення попередньої команди."
        )
    messages = [
        {"role": "system", "content": _build_system_prompt(commands)},
        {"role": "user", "content": user_content},
    ]
    body = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": cfg["temperature"],
        "stream": False,
        "format": "json",
    }
    try:
        resp = requests.post(
            _chat_url(cfg),
            json=body,
            timeout=cfg["timeout_sec"],
            headers={"Content-Type": "application/json"},
        )
        if resp.status_code >= 400:
            print(f"Local LLM HTTP {resp.status_code}: {resp.text[:200]}")
            return []
        data = resp.json()
        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        parsed = _extract_json(str(content))
        if parsed is None:
            print(f"Local LLM bad JSON: {str(content)[:200]}")
            return []
        mapped = _map_llm_commands(parsed, command_by_id, utterance)
        if cfg["use_context"]:
            _RECENT_UTTERANCES.append(utterance)
        if mapped:
            _LAST_LLM_COMMANDS = [dict(item) for item in mapped]
        _log_mapped(utterance, mapped)
        return mapped
    except requests.RequestException as e:
        print(f"Local LLM unavailable: {e}")
        return []
    except Exception as e:
        print(f"Local LLM parse skipped: {e}")
        return []
