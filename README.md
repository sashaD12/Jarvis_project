# Jarvis / R.I.A.T.

Desktop voice/text assistant (Python + Tkinter) with multilingual speech recognition (faster-whisper), cipher tool, news, and map.

## Requirements

- Python 3.13+ (see `Start_Jarvis.bat`)
- Microphone
- Internet on first run (Whisper model download into Hugging Face cache)

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Copy env file and set secrets:

```bash
copy .env.example .env
```

Edit `.env`:

```text
NEWS_API_KEY=your_key_from_newsapi.org
WHISPER_MODEL_SIZE=
WHISPER_DEVICE=
```

Optional env overrides for Whisper (otherwise values from `settings.json` → `whisper`):

- `WHISPER_MODEL_SIZE` — e.g. `tiny`, `base`, `small`, `medium`
- `WHISPER_DEVICE` — e.g. `cpu` or `cuda`

Default model is `small` on CPU (`int8`). First microphone use downloads the model automatically.

## Run

```bat
Start_Jarvis.bat
```

Or:

```bash
py -3.13 Start_Jarvis_Program.py
```

Quick mic test (speak, then pause ~2s):

```bash
py -3.13 microphone_capture.py
```

## Voice / text commands

Wake word (default): `атас` — configured in `settings.json`.

Examples:

- `атас котра година`
- `атас відкрий браузер`
- `атас open youtube`
- `атас включи музику shape of you`
- `атас покажи погоду`
- `атас відкрий блокнот`
- `атас вимкни комп'ютер` (asks for confirmation)

Stop listening phrases: `шухер` or `стоп` (`settings.json` → `stop_words`). Recording also stops after silence or UI stop button.

On the Jarvis page, press **Start Jarvis: ON** before text/mic commands are executed.

## Configure commands via JSON

### `settings.json`

- `wake_word` — activation phrase
- `stop_words` — stop phrases in transcribed text
- `weather.lat` / `weather.lon` — Open-Meteo location
- `save_training_data` — save mic clips under `training_data/`
- `whisper.model_size` / `device` / `compute_type` / `language` / `max_record_sec`
  - `language: null` = auto-detect (Ukrainian + English in one phrase)
- `llm` — local LLM command parser (Ollama / LM Studio)
  - `enabled`, `provider` (`ollama` | `openai_compat`), `base_url`, `model`
  - `prefer_over_keywords: true` — LLM result wins when available

### Local LLM (Ollama)

1. Install [Ollama](https://ollama.com/download)
2. `ollama pull llama3.2`
3. Keep Ollama running (`ollama serve` if needed)
4. Defaults in `settings.json` → `llm` already point to `http://127.0.0.1:11434`

LM Studio: set `"provider": "openai_compat"`, `"base_url": "http://127.0.0.1:1234/v1"`, and your loaded model name.

If the LLM is offline, Jarvis falls back to keywords + neural embeddings.

### `commands.json`

Each command:

| Field | Meaning |
|-------|---------|
| `id` | unique id |
| `keywords` | exact/fuzzy phrases to match |
| `examples` | natural-language phrases for neural intent |
| `priority` | higher wins on overlap |
| `action` | handler name in code |
| `params` | action parameters (e.g. `url`) |

`programs` maps spoken names to executables for `open_program`.

The parser order: local LLM (if online) → keywords → neural command check.

Example — add a new URL command without Python changes:

```json
{
  "id": "open_github",
  "keywords": ["відкрий гітхаб", "github"],
  "examples": ["відкрий гітхаб", "давай гітхаб", "хочу на github"],
  "priority": 5,
  "action": "open_url",
  "params": { "url": "https://github.com" }
}
```

Restart the app after editing JSON.

Built-in actions: `open_url`, `youtube_search`, `show_time`, `weather`, `shutdown`, `open_program`.

## Modules

| File | Role |
|------|------|
| `Start_Jarvis_Program.py` | launcher + boot screen |
| `Jarvis.py` | main UI pages |
| `modul_jarvis.py` | command parser |
| `backend_actions.py` | command actions |
| `config_loader.py` | JSON settings/commands |
| `neural_parser.py` | neural intent + text/program refinement |
| `local_llm.py` | local LLM command parser (Ollama/LM Studio) |
| `microphone_capture.py` | faster-whisper capture |
| `map.py` | map page |
| `backend_cipher.py` | cipher |
| `backend_news.py` | NewsAPI |
