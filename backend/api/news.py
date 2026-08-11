from __future__ import annotations

import asyncio

from fastapi import APIRouter

from backend_news import NewsBackend

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/")
async def get_news() -> dict[str, str]:
    backend = NewsBackend()
    text = await asyncio.to_thread(backend.fetch_news)
    return {"text": text}
