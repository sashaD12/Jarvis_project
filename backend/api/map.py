from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend import map_store

router = APIRouter(prefix="/api/map", tags=["map"])


class MarkerCreate(BaseModel):
    lat: float
    lon: float
    text: str = Field(..., min_length=1)


class MarkerUpdate(BaseModel):
    text: str = Field(..., min_length=1)


class MarkersReplace(BaseModel):
    markers: list[MarkerCreate]


class ViewportBody(BaseModel):
    lat: float
    lon: float
    zoom: int = Field(..., ge=1, le=20)


@router.get("/markers")
def get_markers() -> dict[str, Any]:
    return {"markers": map_store.load_markers()}


@router.put("/markers")
def put_markers(body: MarkersReplace) -> dict[str, Any]:
    markers = [
        {"lat": m.lat, "lon": m.lon, "text": m.text, "id": str(i)}
        for i, m in enumerate(body.markers)
    ]
    return {"markers": map_store.save_markers(markers)}


@router.post("/markers")
def create_marker(body: MarkerCreate) -> dict[str, Any]:
    marker = map_store.add_marker(body.lat, body.lon, body.text)
    return {"marker": marker}


@router.patch("/markers/{marker_id}")
def patch_marker(marker_id: str, body: MarkerUpdate) -> dict[str, Any]:
    marker = map_store.update_marker(marker_id, body.text)
    if marker is None:
        raise HTTPException(status_code=404, detail="Marker not found")
    return {"marker": marker}


@router.delete("/markers/{marker_id}")
def remove_marker(marker_id: str) -> dict[str, bool]:
    ok = map_store.delete_marker(marker_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Marker not found")
    return {"ok": True}


@router.get("/viewport")
def get_viewport() -> dict[str, Any]:
    return map_store.load_viewport()


@router.put("/viewport")
def put_viewport(body: ViewportBody) -> dict[str, Any]:
    return map_store.save_viewport(body.lat, body.lon, body.zoom)


@router.delete("/data")
def clean_data() -> dict[str, bool]:
    map_store.clean_map_data()
    return {"ok": True}
