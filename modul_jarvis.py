import time
import re
import sys
from typing import Any, Callable

from config_loader import load_commands, load_settings
from backend_actions import run_action, ActionResult
from text_normalizer import (
    compact_text,
    latin_to_cyr_approx,
    levenshtein,
    normalize_recognized_text,
)

sys.stdout.reconfigure(encoding="utf-8")

StatusFn = Callable[[str], None]
ConfirmFn = Callable[[str, str], bool]


def fuzzy_keyword_spans(text: str, keyword: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for match in re.finditer(re.escape(keyword), text):
        spans.append(match.span())

    key_tokens = keyword.split()
    text_tokens = text.split()
    if not key_tokens or not text_tokens:
        return spans

    key_compact = compact_text(keyword)
    if len(key_compact) <= 3:
        return spans
    max_dist = 2 if len(key_compact) <= 8 else 1
    max_window = max(len(key_tokens), 3)

    for i in range(len(text_tokens)):
        for n in range(len(key_tokens), min(max_window, len(text_tokens) - i) + 1):
            window = text_tokens[i:i + n]
            window_text = " ".join(window)
            variants = [
                compact_text(window_text),
                compact_text(latin_to_cyr_approx(window_text)),
            ]
            matched = any(levenshtein(variant, key_compact) <= max_dist for variant in variants)
            if not matched and len(key_tokens) == 1 and n == 1:
                token = window[0]
                stem = key_compact[:4]
                token_compact = compact_text(token)
                token_cyr = compact_text(latin_to_cyr_approx(token))
                matched = bool(
                    stem
                    and len(token) >= 4
                    and (
                        stem in token_compact
                        or stem in token_cyr
                        or levenshtein(token_compact, key_compact) <= max_dist
                        or levenshtein(token_cyr, key_compact) <= max_dist
                    )
                )
            if matched:
                prefix = " ".join(text_tokens[:i])
                start = len(prefix) + (1 if prefix else 0)
                end = start + len(window_text)
                spans.append((start, end))

    unique: list[tuple[int, int]] = []
    for span in sorted(spans):
        if not unique or span != unique[-1]:
            unique.append(span)
    return unique


class Jarvis:
    def __init__(
        self,
        text: str,
        status_callback: StatusFn | None = None,
        confirm_callback: ConfirmFn | None = None,
        execute: bool = True,
    ):
        self.status_callback = status_callback
        self.confirm_callback = confirm_callback
        self.settings = load_settings()
        commands_data = load_commands()
        self.commands = commands_data["commands"]
        self.programs = commands_data["programs"]
        self.command_by_id = {c["id"]: c for c in self.commands}
        self.results: list[ActionResult] = []
        cmds = self.recognize_commands(text)
        if execute:
            self.execute_commands(cmds)

    def _status(self, message: str) -> None:
        print(message)
        if self.status_callback is not None:
            self.status_callback(message)

    def extract_after_keyword(self, text: str, keyword_pos: int, keyword: str) -> str | None:
        after = text[keyword_pos + len(keyword):]
        value = re.split(
            r"\s+(через|потім|і|та|далі|вимкни|відкрий|покажи|запусти|включи)\s+",
            after,
        )[0].strip()
        return value if value else None

    def recognize_commands(self, text: str) -> list[dict[str, Any]]:
        wake_word = self.settings["wake_word"]
        aliases = self.settings.get("wake_word_aliases", [])
        text = normalize_recognized_text(text, wake_word, aliases)
        try:
            from neural_parser import neural_refine_text

            text = neural_refine_text(text)
        except Exception:
            pass
        trigger_pos = text.find(wake_word)
        if trigger_pos == -1:
            self._status("Система не активована. Потрібне wake-слово.")
            return []

        text = text[trigger_pos + len(wake_word):].strip()
        text = re.sub(r"^[а-яa-zієїґ]\s+", "", text, flags=re.IGNORECASE).strip()

        llm_hits: list[dict[str, Any]] = []
        llm_cfg = self.settings.get("llm")
        if isinstance(llm_cfg, dict) and llm_cfg.get("enabled", True):
            try:
                from local_llm import llm_parse_commands

                llm_hits = llm_parse_commands(text)
                if llm_hits and bool(llm_cfg.get("prefer_over_keywords", True)):
                    self._status_commands(llm_hits)
                    return llm_hits
            except Exception as e:
                self._status(f"Local LLM skipped: {e}")

        found_raw: list[tuple[int, int, str, str, int]] = []

        for cmd in self.commands:
            for word in cmd["keywords"]:
                for start, end in fuzzy_keyword_spans(text, word):
                    found_raw.append((start, end, cmd["id"], word, cmd["priority"]))

        found_raw.sort(key=lambda x: (x[0], -x[4]))

        filtered: list[tuple[int, int, str, str, int]] = []
        for start, end, cmd, word, pr in found_raw:
            overlap = False
            for i, (fs, fe, fcmd, fword, fpr) in enumerate(filtered):
                if not (end <= fs or start >= fe):
                    if pr > fpr:
                        filtered[i] = (start, end, cmd, word, pr)
                    overlap = True
                    break
            if not overlap:
                filtered.append((start, end, cmd, word, pr))

        result: list[dict[str, Any]] = []
        ordered = sorted(filtered, key=lambda x: x[0])
        for i, (start, end, cmd_id, keyword, pr) in enumerate(ordered):
            delay = 0
            if i > 0:
                prev_end = ordered[i - 1][1]
                fragment = text[prev_end:start]
                match = re.search(
                    r"через\s+(\d+)\s*(секунд|секунди|секунда|хвилин|хвилини|хвилину|годин)?",
                    fragment,
                )
                if match:
                    num = int(match.group(1))
                    unit = match.group(2)
                    if unit and "хв" in unit:
                        delay = num * 60
                    elif unit and "год" in unit:
                        delay = num * 3600
                    else:
                        delay = num

            cmd_def = self.command_by_id[cmd_id]
            action = cmd_def["action"]
            song = None
            program = None
            if action == "youtube_search":
                song = self.extract_after_keyword(text, start, keyword)
            elif action == "open_program":
                program = self.extract_after_keyword(text, start, keyword)

            result.append(
                {
                    "command": cmd_id,
                    "action": action,
                    "params": cmd_def.get("params", {}),
                    "priority": pr,
                    "keyword": keyword,
                    "delay": delay,
                    "song": song,
                    "program": program,
                    "source": "keyword",
                }
            )

        result = self._merge_neural_commands(text, result)
        if not result and llm_hits:
            result = llm_hits

        self._status_commands(result)
        return result

    def _status_commands(self, result: list[dict[str, Any]]) -> None:
        if result:
            self._status("Знайдені команди:")
            for f in result:
                delay_info = f", затримка: {f['delay']} сек" if f["delay"] else ""
                song_info = f", пісня: '{f['song']}'" if f.get("song") else ""
                program_info = f", програма: '{f['program']}'" if f.get("program") else ""
                source_info = f", джерело: {f.get('source', 'keyword')}"
                conf = f.get("confidence")
                conf_info = f", впевненість: {conf}" if conf is not None else ""
                reason = f.get("reason")
                reason_info = f", сенс: {reason}" if reason else ""
                self._status(
                    f" - {f['command']} (ключове слово: '{f['keyword']}'{delay_info}{song_info}{program_info}{source_info}{conf_info}{reason_info}, пріоритет: {f['priority']})"
                )
        else:
            self._status("Команд не знайдено.")

    def _merge_neural_commands(
        self,
        text: str,
        result: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        neural_cfg = self.settings.get("neural")
        if not isinstance(neural_cfg, dict) or not neural_cfg.get("enabled", True):
            return result
        try:
            from neural_parser import neural_find_commands

            neural_hits = neural_find_commands(text)
        except Exception:
            return result
        if not neural_hits:
            return result

        by_id = {str(item.get("command")): item for item in result}
        for hit in neural_hits:
            cmd_id = str(hit.get("command"))
            existing = by_id.get(cmd_id)
            if existing is not None:
                existing["source"] = "keyword+neural"
                existing["confidence"] = hit.get("confidence")
                if not existing.get("program") and hit.get("program"):
                    existing["program"] = hit["program"]
                if not existing.get("song") and hit.get("song"):
                    existing["song"] = hit["song"]

        if result:
            return result

        if not neural_hits:
            return result

        best = max(neural_hits, key=lambda item: float(item.get("confidence") or 0.0))
        if best.get("action") == "open_program" and best.get("program"):
            return [best]
        if float(best.get("confidence") or 0.0) >= 0.72:
            return [best]
        return result

    def execute_commands(self, found: list[dict[str, Any]]) -> list[ActionResult]:
        found_sorted = sorted(found, key=lambda f: f["priority"], reverse=True)
        self.results = []
        self._status("Виконання команд за пріоритетом:")
        for f in found_sorted:
            delay = f["delay"]
            if delay > 0:
                self._status(f"Очікую {delay} сек перед виконанням '{f['command']}'...")
                time.sleep(delay)
            self._status(f"Виконую {f['command']} ({f['action']})...")
            context: dict[str, Any] = {
                "settings": self.settings,
                "programs": self.programs,
                "song": f.get("song"),
                "program": f.get("program"),
                "confirm": self.confirm_callback,
            }
            result = run_action(f["action"], f.get("params", {}), context)
            self.results.append(result)
            self._status(result.message)
            time.sleep(0.3)
        return self.results
