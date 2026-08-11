from __future__ import annotations

import os
import sys
import threading
import time
import urllib.error
import urllib.request

import uvicorn
import webview
from dotenv import load_dotenv

from config_loader import BASE_DIR

load_dotenv(os.path.join(BASE_DIR, ".env"))

HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}/"


class DesktopApi:
    def quit(self) -> None:
        for window in webview.windows:
            window.destroy()


def wait_for_server(timeout_sec: float = 60.0) -> bool:
    deadline = time.time() + timeout_sec
    health_url = f"http://{HOST}:{PORT}/api/health"
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(health_url, timeout=1.5) as response:
                if response.status == 200:
                    return True
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.25)
    return False


def run_server() -> None:
    uvicorn.run(
        "backend.main:app",
        host=HOST,
        port=PORT,
        reload=False,
        log_level="warning",
    )


if __name__ == "__main__":
    sys.path.insert(0, BASE_DIR)
    dist_index = os.path.join(BASE_DIR, "frontend", "dist", "index.html")
    if not os.path.isfile(dist_index):
        print("Frontend build missing.")
        print("Run: cd frontend && npm install && npm run build")
        sys.exit(1)

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    if not wait_for_server():
        print("Failed to start R.I.A.T. local server.")
        sys.exit(1)

    api = DesktopApi()
    webview.create_window(
        title="R.I.A.T. Special System",
        url=URL,
        width=1100,
        height=720,
        min_size=(900, 560),
        background_color="#000010",
        js_api=api,
    )
    webview.start()
