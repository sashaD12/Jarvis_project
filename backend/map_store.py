from __future__ import annotations

import json
import os
import uuid
from typing import Any

from config_loader import BASE_DIR

MARKERS_FILE = os.path.join(BASE_DIR, "markers.json")
SETTINGS_FILE = os.path.join(BASE_DIR, "map_settings.json")

DEFAULT_VIEWPORT = {"lat": 50.45, "lon": 30.52, "zoom": 6}


def _normalize_marker(item: dict[str, Any], index: int) -> dict[str, Any]:
    lat = item.get("lat")
    lon = item.get("lon")
    if lat is None or lon is None:
        position = item.get("position", [0, 0])
        lat = position[0]
        lon = position[1]
    marker_id = item.get("id") or str(index)
    return {
        "id": str(marker_id),
        "lat": float(lat),
        "lon": float(lon),
        "text": str(item.get("text", "")),
    }


def load_markers() -> list[dict[str, Any]]:
    if not os.path.exists(MARKERS_FILE):
        return []
    with open(MARKERS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        return []
    return [_normalize_marker(item, i) for i, item in enumerate(data) if isinstance(item, dict)]


def save_markers(markers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for i, item in enumerate(markers):
        normalized.append(_normalize_marker(item, i))
    with open(MARKERS_FILE, "w", encoding="utf-8") as f:
        json.dump(
            [{"lat": m["lat"], "lon": m["lon"], "text": m["text"], "id": m["id"]} for m in normalized],
            f,
            ensure_ascii=False,
            indent=2,
        )
    return normalized


def add_marker(lat: float, lon: float, text: str) -> dict[str, Any]:
    markers = load_markers()
    marker = {
        "id": str(uuid.uuid4()),
        "lat": float(lat),
        "lon": float(lon),
        "text": text.strip(),
    }
    markers.append(marker)
    save_markers(markers)
    return marker


def update_marker(marker_id: str, text: str) -> dict[str, Any] | None:
    markers = load_markers()
    for marker in markers:
        if marker["id"] == marker_id:
            marker["text"] = text.strip()
            save_markers(markers)
            return marker
    return None


def delete_marker(marker_id: str) -> bool:
    markers = load_markers()
    next_markers = [m for m in markers if m["id"] != marker_id]
    if len(next_markers) == len(markers):
        return False
    save_markers(next_markers)
    return True


def load_viewport() -> dict[str, Any]:
    if not os.path.exists(SETTINGS_FILE):
        return dict(DEFAULT_VIEWPORT)
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "lat": float(data.get("lat", DEFAULT_VIEWPORT["lat"])),
            "lon": float(data.get("lon", DEFAULT_VIEWPORT["lon"])),
            "zoom": int(data.get("zoom", DEFAULT_VIEWPORT["zoom"])),
        }
    except Exception:
        return dict(DEFAULT_VIEWPORT)


def save_viewport(lat: float, lon: float, zoom: int) -> dict[str, Any]:
    viewport = {"lat": float(lat), "lon": float(lon), "zoom": int(zoom)}
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(viewport, f, indent=2)
    return viewport


def clean_map_data() -> None:
    for path in (MARKERS_FILE, SETTINGS_FILE):
        try:
            os.remove(path)
        except OSError:
            pass
