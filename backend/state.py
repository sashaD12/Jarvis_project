from __future__ import annotations

import threading
from typing import Any

from backend_cipher import CipherBackend


class AppState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.jarvis_enabled = False
        self.listening = False
        self.listen_stop = False
        self.cipher = CipherBackend()
        self.confirm_events: dict[str, threading.Event] = {}
        self.confirm_results: dict[str, bool] = {}

    def set_power(self, enabled: bool) -> bool:
        with self.lock:
            self.jarvis_enabled = enabled
            return self.jarvis_enabled

    def get_power(self) -> bool:
        with self.lock:
            return self.jarvis_enabled

    def start_listen(self) -> bool:
        with self.lock:
            if self.listening:
                return False
            self.listening = True
            self.listen_stop = False
            return True

    def request_listen_stop(self) -> None:
        with self.lock:
            self.listen_stop = True

    def should_stop_listen(self) -> bool:
        with self.lock:
            return self.listen_stop

    def finish_listen(self) -> None:
        with self.lock:
            self.listening = False
            self.listen_stop = False

    def is_listening(self) -> bool:
        with self.lock:
            return self.listening

    def register_confirm(self, request_id: str) -> threading.Event:
        event = threading.Event()
        with self.lock:
            self.confirm_events[request_id] = event
            self.confirm_results[request_id] = False
        return event

    def resolve_confirm(self, request_id: str, accepted: bool) -> None:
        with self.lock:
            self.confirm_results[request_id] = accepted
            event = self.confirm_events.get(request_id)
        if event is not None:
            event.set()

    def wait_confirm(self, request_id: str, timeout: float = 120.0) -> bool:
        event = self.confirm_events.get(request_id)
        if event is None:
            return False
        event.wait(timeout=timeout)
        with self.lock:
            result = self.confirm_results.pop(request_id, False)
            self.confirm_events.pop(request_id, None)
        return bool(result)

    def cipher_state(self) -> dict[str, Any]:
        c = self.cipher
        return {
            "keyplus": c.keyplus,
            "keyminus": c.keyminus,
            "alfabet": c.alfabet,
            "b": c.b,
        }

    def adjust_cipher_key(self, delta: int) -> dict[str, Any]:
        c = self.cipher
        mod = len(c.alfabet)
        c.keyplus = (c.keyplus + delta) % mod
        if c.keyplus == 0:
            c.keyplus = 1
        c.keyminus = c.find_inverse(c.keyplus, mod)
        return self.cipher_state()


app_state = AppState()
