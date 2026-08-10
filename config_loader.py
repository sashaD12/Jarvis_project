import json
import os
from typing import Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
COMMANDS_FILE = os.path.join(BASE_DIR, "commands.json")

DEFAULT_WHISPER: dict[str, Any] = {
    "model_size": "small",
    "device": "cpu",
    "compute_type": "int8",
    "language": "uk",
    "max_record_sec": 20,
    "beam_size": 5,
    "initial_prompt": "атас запусти відкрий епік геймс stalcraft погода браузер ютуб музика час вимкни стоп шухер",
}

DEFAULT_NEURAL: dict[str, Any] = {
    "enabled": True,
    "model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "text_threshold": 0.52,
    "program_threshold": 0.42,
    "intent_threshold": 0.62,
    "intent_first": True,
}

DEFAULT_LLM: dict[str, Any] = {
    "enabled": True,
    "provider": "ollama",
    "base_url": "http://127.0.0.1:11434",
    "model": "llama3.2",
    "timeout_sec": 90,
    "prefer_over_keywords": True,
    "temperature": 0.1,
    "use_context": True,
}

DEFAULT_SETTINGS: dict[str, Any] = {
    "wake_word": "атас",
    "wake_word_aliases": [
        "атос",
        "ата з",
        "а тас",
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
    ],
    "stop_words": ["шухер", "стоп"],
    "default_city": "Kyiv",
    "weather": {"lat": 50.45, "lon": 30.52},
    "save_training_data": True,
    "whisper": dict(DEFAULT_WHISPER),
    "neural": dict(DEFAULT_NEURAL),
    "llm": dict(DEFAULT_LLM),
}

DEFAULT_COMMANDS: dict[str, Any] = {
    "commands": [
        {
            "id": "open_browser",
            "keywords": ["відкрий браузер", "запусти браузер", "chrome", "browser"],
            "priority": 9,
            "action": "open_url",
            "params": {"url": "https://www.google.com"},
        },
        {
            "id": "youtube",
            "keywords": ["ютуб", "відкрий ютуб", "youtube"],
            "priority": 4,
            "action": "open_url",
            "params": {"url": "https://www.youtube.com"},
        },
        {
            "id": "play_music",
            "keywords": ["включи музику", "включи пісню", "spotify", "music"],
            "priority": 4,
            "action": "youtube_search",
            "params": {"fallback_url": "https://www.youtube.com"},
        },
        {
            "id": "time",
            "keywords": ["котра година", "поточний час", "час"],
            "priority": 3,
            "action": "show_time",
            "params": {},
        },
        {
            "id": "weather",
                "keywords": ["покажи погоду", "погоду", "погода", "прогноз", "температура"],
            "priority": 4,
            "action": "weather",
            "params": {},
        },
        {
            "id": "shutdown",
            "keywords": ["вимкни комп'ютер", "вимкни систему", "shutdown"],
            "priority": 1,
            "action": "shutdown",
            "params": {"delay_sec": 60},
        },
        {
            "id": "open_program",
            "keywords": ["відкрий", "запусти"],
            "priority": 3,
            "action": "open_program",
            "params": {},
        },
    ],
    "programs": {
        "блокнот": "notepad",
        "калькулятор": "calc",
        "провідник": "explorer",
        "cmd": "cmd",
        "chrome": "chrome",
        "edge": "msedge",
    },
}


class ConfigError(Exception):
    pass


def _write_json(path: str, data: dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _read_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ConfigError(f"Файл {path} повинен містити JSON-об'єкт")
    return data


def _ensure_file(path: str, default_data: dict[str, Any]) -> dict[str, Any]:
    if not os.path.exists(path):
        _write_json(path, default_data)
        return default_data
    try:
        return _read_json(path)
    except (json.JSONDecodeError, OSError) as e:
        raise ConfigError(f"Не вдалося прочитати {path}: {e}") from e


def _validate_whisper(data: dict[str, Any]) -> dict[str, Any]:
    whisper = data.get("whisper", DEFAULT_WHISPER)
    if not isinstance(whisper, dict):
        raise ConfigError("settings.json: whisper повинен бути об'єктом")
    model_size = str(whisper.get("model_size", DEFAULT_WHISPER["model_size"])).strip()
    device = str(whisper.get("device", DEFAULT_WHISPER["device"])).strip()
    compute_type = str(whisper.get("compute_type", DEFAULT_WHISPER["compute_type"])).strip()
    if not model_size or not device or not compute_type:
        raise ConfigError("settings.json: whisper потребує model_size, device, compute_type")
    language = whisper.get("language", DEFAULT_WHISPER["language"])
    if language is not None:
        language = str(language).strip() or None
    max_record_sec = float(whisper.get("max_record_sec", DEFAULT_WHISPER["max_record_sec"]))
    if max_record_sec <= 0:
        raise ConfigError("settings.json: whisper.max_record_sec повинен бути > 0")
    beam_size = int(whisper.get("beam_size", DEFAULT_WHISPER["beam_size"]))
    if beam_size < 1:
        raise ConfigError("settings.json: whisper.beam_size повинен бути >= 1")
    initial_prompt = whisper.get("initial_prompt", DEFAULT_WHISPER["initial_prompt"])
    if initial_prompt is None:
        initial_prompt = ""
    return {
        "model_size": model_size,
        "device": device,
        "compute_type": compute_type,
        "language": language,
        "max_record_sec": max_record_sec,
        "beam_size": beam_size,
        "initial_prompt": str(initial_prompt),
    }


def _validate_llm(data: dict[str, Any]) -> dict[str, Any]:
    llm = data.get("llm", DEFAULT_LLM)
    if not isinstance(llm, dict):
        raise ConfigError("settings.json: llm повинен бути об'єктом")
    provider = str(llm.get("provider", DEFAULT_LLM["provider"])).strip().lower()
    if provider not in {"ollama", "openai_compat"}:
        raise ConfigError("settings.json: llm.provider = ollama | openai_compat")
    base_url = str(llm.get("base_url", DEFAULT_LLM["base_url"])).strip().rstrip("/")
    model = str(llm.get("model", DEFAULT_LLM["model"])).strip()
    if not base_url or not model:
        raise ConfigError("settings.json: llm потребує base_url і model")
    return {
        "enabled": bool(llm.get("enabled", True)),
        "provider": provider,
        "base_url": base_url,
        "model": model,
        "timeout_sec": float(llm.get("timeout_sec", DEFAULT_LLM["timeout_sec"])),
        "prefer_over_keywords": bool(
            llm.get("prefer_over_keywords", DEFAULT_LLM["prefer_over_keywords"])
        ),
        "temperature": float(llm.get("temperature", DEFAULT_LLM["temperature"])),
        "use_context": bool(llm.get("use_context", DEFAULT_LLM["use_context"])),
    }


def _validate_neural(data: dict[str, Any]) -> dict[str, Any]:
    neural = data.get("neural", DEFAULT_NEURAL)
    if not isinstance(neural, dict):
        raise ConfigError("settings.json: neural повинен бути об'єктом")
    model = str(neural.get("model", DEFAULT_NEURAL["model"])).strip()
    if not model:
        raise ConfigError("settings.json: neural.model порожній")
    return {
        "enabled": bool(neural.get("enabled", True)),
        "model": model,
        "text_threshold": float(neural.get("text_threshold", DEFAULT_NEURAL["text_threshold"])),
        "program_threshold": float(
            neural.get("program_threshold", DEFAULT_NEURAL["program_threshold"])
        ),
        "intent_threshold": float(
            neural.get("intent_threshold", DEFAULT_NEURAL["intent_threshold"])
        ),
        "intent_first": bool(neural.get("intent_first", DEFAULT_NEURAL["intent_first"])),
    }


def _validate_settings(data: dict[str, Any]) -> dict[str, Any]:
    if "wake_word" not in data or not str(data["wake_word"]).strip():
        raise ConfigError("settings.json: відсутнє поле wake_word")
    stop_words = data.get("stop_words", ["шухер", "стоп"])
    if not isinstance(stop_words, list) or not all(isinstance(w, str) for w in stop_words):
        raise ConfigError("settings.json: stop_words повинен бути списком рядків")
    aliases = data.get("wake_word_aliases", DEFAULT_SETTINGS["wake_word_aliases"])
    if not isinstance(aliases, list) or not all(isinstance(w, str) for w in aliases):
        raise ConfigError("settings.json: wake_word_aliases повинен бути списком рядків")
    weather = data.get("weather", {"lat": 50.45, "lon": 30.52})
    if not isinstance(weather, dict) or "lat" not in weather or "lon" not in weather:
        raise ConfigError("settings.json: weather повинен містити lat і lon")
    return {
        "wake_word": str(data["wake_word"]).strip().lower(),
        "wake_word_aliases": [w.strip().lower() for w in aliases if w.strip()],
        "stop_words": [w.lower() for w in stop_words],
        "default_city": str(data.get("default_city", "Kyiv")),
        "weather": {"lat": float(weather["lat"]), "lon": float(weather["lon"])},
        "save_training_data": bool(data.get("save_training_data", True)),
        "whisper": _validate_whisper(data),
        "neural": _validate_neural(data),
        "llm": _validate_llm(data),
    }


def _validate_commands(data: dict[str, Any]) -> dict[str, Any]:
    commands = data.get("commands")
    if not isinstance(commands, list) or not commands:
        raise ConfigError("commands.json: відсутній непорожній список commands")
    validated: list[dict[str, Any]] = []
    for i, cmd in enumerate(commands):
        if not isinstance(cmd, dict):
            raise ConfigError(f"commands.json: команда #{i + 1} не є об'єктом")
        for field in ("id", "keywords", "priority", "action"):
            if field not in cmd:
                raise ConfigError(f"commands.json: у команди #{i + 1} немає поля {field}")
        keywords = cmd["keywords"]
        if not isinstance(keywords, list) or not keywords or not all(isinstance(k, str) for k in keywords):
            raise ConfigError(f"commands.json: keywords у '{cmd['id']}' повинні бути непорожнім списком рядків")
        params = cmd.get("params", {})
        if not isinstance(params, dict):
            raise ConfigError(f"commands.json: params у '{cmd['id']}' повинен бути об'єктом")
        examples_raw = cmd.get("examples", [])
        examples: list[str] = []
        if examples_raw:
            if not isinstance(examples_raw, list) or not all(
                isinstance(item, str) for item in examples_raw
            ):
                raise ConfigError(
                    f"commands.json: examples у '{cmd['id']}' повинні бути списком рядків"
                )
            examples = [item.strip().lower() for item in examples_raw if item.strip()]
        intent = str(cmd.get("intent") or "").strip()
        validated.append(
            {
                "id": str(cmd["id"]),
                "intent": intent,
                "keywords": [k.lower() for k in keywords],
                "examples": examples,
                "priority": int(cmd["priority"]),
                "action": str(cmd["action"]),
                "params": params,
            }
        )
    programs = data.get("programs", {})
    if not isinstance(programs, dict):
        raise ConfigError("commands.json: programs повинен бути об'єктом")
    programs_norm = {str(k).lower(): str(v) for k, v in programs.items()}
    return {"commands": validated, "programs": programs_norm}


def load_settings() -> dict[str, Any]:
    raw = _ensure_file(SETTINGS_FILE, DEFAULT_SETTINGS)
    return _validate_settings(raw)


def load_commands() -> dict[str, Any]:
    raw = _ensure_file(COMMANDS_FILE, DEFAULT_COMMANDS)
    return _validate_commands(raw)


def get_whisper_settings() -> dict[str, Any]:
    settings = load_settings()
    whisper = dict(settings["whisper"])
    env_model = os.environ.get("WHISPER_MODEL_SIZE", "").strip()
    env_device = os.environ.get("WHISPER_DEVICE", "").strip()
    if env_model:
        whisper["model_size"] = env_model
    if env_device:
        whisper["device"] = env_device
    return whisper
