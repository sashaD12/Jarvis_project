# Jarvis / R.I.A.T.

Desktop voice/text assistant: native Windows window (pywebview) + React UI + local FastAPI (faster-whisper, cipher, news, map).

## Stack

- **Desktop shell:** pywebview (native app window, not a browser tab)
- **UI:** React + Vite + TypeScript + Tailwind (`frontend/`)
- **API:** FastAPI + WebSocket (`backend/`) on localhost inside the app
- **Theme:** R.I.A.T. tactical (`#000010` / `#00FFCC`)

## Requirements

- Python 3.13+
- Node.js 20+ (build UI once)
- Microsoft Edge WebView2 runtime (usually already on Windows 10/11)
- Microphone
- Internet on first Whisper model download

## Setup

1. Python deps:

```bash
py -3.13 -m pip install -r requirements.txt
```

2. Build the UI (once, or after frontend changes):

```bash
cd frontend
npm install
npm run build
cd ..
```

3. Env:

```bash
copy .env.example .env
```

```text
NEWS_API_KEY=your_key_from_newsapi.org
WHISPER_MODEL_SIZE=
WHISPER_DEVICE=
```

## Run

```bat
Start_Jarvis.bat
```

Opens a **desktop window** titled `R.I.A.T. Special System`. The bat file builds the UI if `frontend/dist` is missing.

Or:

```bash
py -3.13 Start_Jarvis_Program.py
```

Dev UI (optional, browser for styling only):

```bash
py -3.13 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
cd frontend
npm run dev
```

## UI modules

| Route | Role |
|-------|------|
| `/boot` | Boot sequence |
| `/menu` | Navigation + news |
| `/jarvis` | Power, text/mic commands, status log |
| `/cipher` | Encode/decode + key recover |
| `/map` | Leaflet map + markers |

## Voice / text commands

Wake word (default): `атас` — in `settings.json`.

Examples:

- `атас котра година`
- `атас відкрий браузер`
- `атас open youtube`
- `атас включи музику shape of you`
- `атас покажи погоду`
- `атас відкрий блокнот`
- `атас вимкни комп'ютер` (confirmation modal)

Stop phrases: `шухер` / `стоп`. On the Jarvis page, set **Start Jarvis: ON** before commands run.

Mic capture stays on the Python host (PyAudio) via WebSocket `/ws/jarvis`.

## Configure via JSON

### `settings.json`

- `wake_word`, `stop_words`
- `weather.lat` / `weather.lon`
- `whisper.*`, `neural.*`, `llm.*`

### Local LLM (Ollama)

1. Install [Ollama](https://ollama.com/download)
2. `ollama pull llama3.2`
3. Defaults in `settings.json` → `llm` point to `http://127.0.0.1:11434`

If the LLM is offline, Jarvis falls back to keywords + neural embeddings.

### `commands.json`

| Field | Meaning |
|-------|---------|
| `id` | unique id |
| `keywords` | exact/fuzzy phrases |
| `examples` | neural intent phrases |
| `priority` | higher wins |
| `action` | handler name |
| `params` | action parameters |

Parser order: local LLM → keywords → neural.

Built-in actions: `open_url`, `youtube_search`, `show_time`, `weather`, `shutdown`, `open_program`.

## Project layout

| Path | Role |
|------|------|
| `backend/main.py` | FastAPI app |
| `backend/api/` | REST routes |
| `backend/ws/` | Jarvis WebSocket |
| `frontend/` | React UI |
| `modul_jarvis.py` | command parser |
| `backend_actions.py` | OS/web actions |
| `microphone_capture.py` | Whisper capture |
| `Jarvis.py` / `intro.py` / `map.py` | legacy Tkinter (unused by launcher) |
