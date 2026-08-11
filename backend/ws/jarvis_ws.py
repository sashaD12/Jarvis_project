from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.state import app_state
from microphone_capture import capture_text_from_microphone
from modul_jarvis import Jarvis

router = APIRouter(tags=["websocket"])


async def _send(ws: WebSocket, event: str, payload: dict[str, Any] | None = None) -> None:
    message = {"event": event}
    if payload:
        message.update(payload)
    await ws.send_text(json.dumps(message, ensure_ascii=False))


@router.websocket("/ws/jarvis")
async def jarvis_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    loop = asyncio.get_running_loop()
    listen_task: asyncio.Task[None] | None = None

    async def emit(event: str, payload: dict[str, Any] | None = None) -> None:
        try:
            await _send(websocket, event, payload)
        except Exception:
            pass

    def status_callback(message: str) -> None:
        asyncio.run_coroutine_threadsafe(emit("status", {"message": message}), loop)

    def confirm_callback(title: str, message: str) -> bool:
        request_id = str(uuid.uuid4())
        app_state.register_confirm(request_id)
        fut = asyncio.run_coroutine_threadsafe(
            emit(
                "confirm.request",
                {"request_id": request_id, "title": title, "message": message},
            ),
            loop,
        )
        try:
            fut.result(timeout=5)
        except Exception:
            pass
        return app_state.wait_confirm(request_id, timeout=120.0)

    async def run_listen() -> None:
        await emit("listen.state", {"listening": True})
        await emit("status", {"message": "Слухаю..."})

        def capture() -> str:
            return capture_text_from_microphone(should_stop=app_state.should_stop_listen)

        try:
            text = await asyncio.to_thread(capture)
            if text:
                await emit("transcript", {"text": text})
                await emit("status", {"message": f"Розпізнано: {text}"})
                if app_state.get_power():
                    def run_jarvis() -> None:
                        Jarvis(
                            text,
                            status_callback=status_callback,
                            confirm_callback=confirm_callback,
                            execute=True,
                        )

                    await asyncio.to_thread(run_jarvis)
                else:
                    await emit("status", {"message": "Jarvis вимкнено. Натисніть Start Jarvis."})
            else:
                await emit("status", {"message": "Нічого не розпізнано."})
        except Exception as exc:
            await emit("error", {"message": f"Помилка розпізнавання: {exc}"})
        finally:
            app_state.finish_listen()
            await emit("listen.state", {"listening": False})
            await emit("status", {"message": "Мікрофон зупинено."})

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await emit("error", {"message": "Invalid JSON"})
                continue

            event = data.get("event")
            if event == "listen.start":
                if listen_task is not None and not listen_task.done():
                    await emit("status", {"message": "Мікрофон вже активний"})
                    continue
                if not app_state.start_listen():
                    await emit("status", {"message": "Мікрофон вже активний"})
                    continue
                listen_task = asyncio.create_task(run_listen())
            elif event == "listen.stop":
                app_state.request_listen_stop()
                await emit("status", {"message": "Зупинка мікрофона..."})
            elif event == "confirm.response":
                request_id = str(data.get("request_id", ""))
                accepted = bool(data.get("accepted", False))
                if request_id:
                    app_state.resolve_confirm(request_id, accepted)
            elif event == "jarvis.process":
                text = str(data.get("text", "")).strip()
                execute = bool(data.get("execute", True))
                if not app_state.get_power():
                    await emit("status", {"message": "Jarvis вимкнено. Натисніть Start Jarvis."})
                    continue
                if not text:
                    await emit("status", {"message": "Порожній текст."})
                    continue

                def run_process() -> None:
                    jarvis = Jarvis(
                        text,
                        status_callback=status_callback,
                        confirm_callback=confirm_callback,
                        execute=execute,
                    )
                    for result in jarvis.results:
                        asyncio.run_coroutine_threadsafe(
                            emit("result", {"message": result.message, "ok": result.ok}),
                            loop,
                        )

                await asyncio.to_thread(run_process)
            else:
                await emit("error", {"message": f"Unknown event: {event}"})
    except WebSocketDisconnect:
        app_state.request_listen_stop()
        if listen_task is not None and not listen_task.done():
            listen_task.cancel()
