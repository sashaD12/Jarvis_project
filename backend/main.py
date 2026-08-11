from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config_loader import BASE_DIR

load_dotenv(os.path.join(BASE_DIR, ".env"))

from backend.api import cipher, health, jarvis, map as map_api, news
from backend.ws import jarvis_ws

DIST_DIR = os.path.join(ROOT, "frontend", "dist")
ASSETS_DIR = os.path.join(DIST_DIR, "assets")

app = FastAPI(title="R.I.A.T. API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:4173",
        "http://localhost:4173",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(jarvis.router)
app.include_router(cipher.router)
app.include_router(news.router)
app.include_router(map_api.router)
app.include_router(jarvis_ws.router)

if os.path.isdir(ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")


def missing_frontend() -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "error": "Frontend build missing",
            "hint": "Run: cd frontend && npm install && npm run build",
        },
    )


@app.get("/", response_model=None)
def spa_index():
    index_path = os.path.join(DIST_DIR, "index.html")
    if not os.path.isfile(index_path):
        return missing_frontend()
    return FileResponse(index_path)


@app.get("/favicon.svg", response_model=None)
def favicon():
    path = os.path.join(DIST_DIR, "favicon.svg")
    if os.path.isfile(path):
        return FileResponse(path)
    public = os.path.join(ROOT, "frontend", "public", "favicon.svg")
    if os.path.isfile(public):
        return FileResponse(public)
    return JSONResponse(status_code=404, content={"error": "Not found"})
