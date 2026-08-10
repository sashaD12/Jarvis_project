import os
import subprocess
import urllib.parse
import webbrowser
from datetime import datetime
from typing import Any, Callable

import requests

from config_loader import load_commands, load_settings


class ActionResult:
    def __init__(self, message: str, ok: bool = True):
        self.message = message
        self.ok = ok


ConfirmFn = Callable[[str, str], bool]


def action_open_url(params: dict[str, Any], context: dict[str, Any]) -> ActionResult:
    url = params.get("url")
    if not url:
        return ActionResult("URL не вказано у params", ok=False)
    webbrowser.open(str(url))
    return ActionResult(f"Відкрито: {url}")


def action_youtube_search(params: dict[str, Any], context: dict[str, Any]) -> ActionResult:
    song = context.get("song")
    if song:
        query = urllib.parse.quote_plus(str(song))
        url = f"https://www.youtube.com/results?search_query={query}"
        webbrowser.open(url)
        return ActionResult(f"Шукаю на YouTube: {song}")
    fallback = params.get("fallback_url", "https://www.youtube.com")
    webbrowser.open(str(fallback))
    return ActionResult("Відкрито YouTube")


def action_show_time(params: dict[str, Any], context: dict[str, Any]) -> ActionResult:
    now = datetime.now().strftime("%H:%M:%S")
    return ActionResult(f"Поточний час: {now}")


def action_weather(params: dict[str, Any], context: dict[str, Any]) -> ActionResult:
    settings = context.get("settings") or load_settings()
    weather_cfg = settings.get("weather", {"lat": 50.45, "lon": 30.52})
    lat = weather_cfg.get("lat", 50.45)
    lon = weather_cfg.get("lon", 30.52)
    city = settings.get("default_city", "Kyiv")
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
        "&timezone=auto"
    )
    try:
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        current = data.get("current", {})
        temp = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        wind = current.get("wind_speed_10m")
        msg = (
            f"Погода ({city}): {temp}°C, "
            f"вологість {humidity}%, вітер {wind} км/г"
        )
        return ActionResult(msg)
    except Exception as e:
        return ActionResult(f"Не вдалося отримати погоду: {e}", ok=False)


def action_shutdown(params: dict[str, Any], context: dict[str, Any]) -> ActionResult:
    delay = int(params.get("delay_sec", 60))
    confirm = context.get("confirm")
    if callable(confirm):
        accepted = confirm(
            "Shutdown",
            f"Вимкнути комп'ютер через {delay} сек?",
        )
        if not accepted:
            return ActionResult("Вимкнення скасовано")
    try:
        subprocess.run(["shutdown", "/s", "/t", str(delay)], check=False)
        return ActionResult(f"Вимкнення заплановано через {delay} сек (скасувати: shutdown /a)")
    except Exception as e:
        return ActionResult(f"Помилка вимкнення: {e}", ok=False)


def action_open_program(params: dict[str, Any], context: dict[str, Any]) -> ActionResult:
    from program_finder import launch_target, resolve_program

    program_name = str(context.get("program") or "").strip().lower()
    if not program_name:
        return ActionResult("Не вказано назву програми", ok=False)
    programs = context.get("programs")
    if programs is None:
        programs = load_commands().get("programs", {})

    resolved = resolve_program(program_name, programs)
    if resolved is None:
        return ActionResult(
            f"Не знайшов програму '{program_name}'. Спробуй точнішу назву.",
            ok=False,
        )

    target = str(resolved["path"])
    source = str(resolved.get("source", "path"))
    try:
        launch_target(target, source=source)
        shown = str(resolved.get("name") or target)
        query = resolved.get("query")
        extra = f" (запит: {query})" if query and query != program_name else ""
        return ActionResult(f"Запущено: {shown}{extra}")
    except Exception as e:
        return ActionResult(f"Не вдалося запустити '{target}': {e}", ok=False)


ACTIONS: dict[str, Callable[[dict[str, Any], dict[str, Any]], ActionResult]] = {
    "open_url": action_open_url,
    "youtube_search": action_youtube_search,
    "show_time": action_show_time,
    "weather": action_weather,
    "shutdown": action_shutdown,
    "open_program": action_open_program,
}


def run_action(action_name: str, params: dict[str, Any], context: dict[str, Any]) -> ActionResult:
    handler = ACTIONS.get(action_name)
    if handler is None:
        return ActionResult(f"Невідома дія: {action_name}", ok=False)
    return handler(params, context)
