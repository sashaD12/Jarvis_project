from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.state import app_state
from modul_jarvis import Jarvis

router = APIRouter(prefix="/api/jarvis", tags=["jarvis"])


class PowerBody(BaseModel):
    enabled: bool


class ProcessBody(BaseModel):
    text: str
    execute: bool = True


@router.get("/power")
def get_power() -> dict[str, bool]:
    return {"enabled": app_state.get_power()}


@router.post("/power")
def set_power(body: PowerBody) -> dict[str, bool]:
    enabled = app_state.set_power(body.enabled)
    return {"enabled": enabled}


@router.post("/process")
async def process_command(body: ProcessBody) -> dict[str, Any]:
    if not app_state.get_power():
        raise HTTPException(status_code=400, detail="Jarvis is powered off")
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty text")

    def run() -> dict[str, Any]:
        status_messages: list[str] = []

        def status_callback(message: str) -> None:
            status_messages.append(message)

        jarvis = Jarvis(
            text,
            status_callback=status_callback,
            confirm_callback=None,
            execute=body.execute,
        )
        results = [{"message": r.message, "ok": r.ok} for r in jarvis.results]
        return {
            "results": results,
            "status": status_messages,
        }

    return await asyncio.to_thread(run)
