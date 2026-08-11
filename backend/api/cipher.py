from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.state import app_state

router = APIRouter(prefix="/api/cipher", tags=["cipher"])


class KeyBody(BaseModel):
    delta: int = Field(..., description="+1 or -1")


class ProcessBody(BaseModel):
    text: str
    mode: Literal["encode", "decode"]


class RecoverBody(BaseModel):
    numbers: list[int]


@router.get("/state")
def get_state() -> dict[str, Any]:
    return app_state.cipher_state()


@router.post("/key")
def adjust_key(body: KeyBody) -> dict[str, Any]:
    if body.delta not in (-1, 1):
        raise HTTPException(status_code=400, detail="delta must be +1 or -1")
    return app_state.adjust_cipher_key(body.delta)


@router.post("/process")
def process_text(body: ProcessBody) -> dict[str, str]:
    result = app_state.cipher.process_text(body.text.lower(), body.mode)
    return {"result": result}


@router.post("/recover")
def recover_cipher(body: RecoverBody) -> dict[str, str]:
    if len(body.numbers) != 4:
        raise HTTPException(status_code=400, detail="Exactly 4 numbers required")
    result = app_state.cipher.recover_cipher(body.numbers)
    return {"result": result}
