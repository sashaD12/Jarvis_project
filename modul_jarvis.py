import time
from datetime import datetime
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

class Jarvis:
    COMMANDS = {
        "open_browser": {"keywords": ["відкрий браузер", "запусти браузер", "chrome", "browser"], "priority": 9},
        "play_music": {"keywords": ["включи музику", "включи пісню", "spotify", "music"], "priority": 4},
        "time": {"keywords": ["котра година", "поточний час", "час"], "priority": 3},
        "weather": {"keywords": ["покажи погоду", "погоду", "прогноз", "температура"], "priority": 4},
        "shutdown": {"keywords": ["вимкни комп'ютер", "вимкни систему", "shutdown"], "priority": 1},
        "open_program": {"keywords": ["відкрий", "запусти"], "priority": 3},
        "youtube": {"keywords": ["ютуб", "відкрий ютуб", "youtube"], "priority": 4}
    }

    def extract_song_name(self, text, keyword_pos, keyword):
        after = text[keyword_pos + len(keyword):]
        song = re.split(r"\s+(через|потім|і|та|далі|вимкни|відкрий|покажи|запусти)\s+", after)[0].strip()
        return song if song else None

    def recognize_commands(self, text):
        text = text.lower()
        system_trigger = "атас"
        trigger_pos = text.find(system_trigger)
        if trigger_pos == -1:
            print(" Система не активирована. Игнорирую команды.")
            return []

        text = text[trigger_pos + len(system_trigger):].strip()
        found_raw = []

        for cmd, data in self.COMMANDS.items():
            for word in data["keywords"]:
                for match in re.finditer(re.escape(word), text):
                    start, end = match.span()
                    found_raw.append((start, end, cmd, word, data["priority"]))

        found_raw.sort(key=lambda x: (x[0], -x[4]))

        filtered = []
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

        result = []
        for i, (start, end, cmd, keyword, pr) in enumerate(sorted(filtered, key=lambda x: x[0])):
            delay = 0
            if i > 0:
                prev_end = filtered[i-1][1]
                fragment = text[prev_end:start]
                match = re.search(r"через\s+(\d+)\s*(секунд|секунди|секунда|хвилин|хвилини|хвилину|годин)?", fragment)
                if match:
                    num = int(match.group(1))
                    unit = match.group(2)
                    if unit and "хв" in unit:
                        delay = num * 60
                    elif unit and "год" in unit:
                        delay = num * 3600
                    else:
                        delay = num

            song_name = self.extract_song_name(text, start, keyword) if cmd == "play_music" else None
            result.append({"command": cmd, "priority": pr, "keyword": keyword, "delay": delay, "song": song_name})

        if result:
            print(" Знайдені команди:")
            for f in result:
                delay_info = f", затримка: {f['delay']} сек" if f['delay'] else ""
                song_info = f", пісня: '{f['song']}'" if f.get("song") else ""
                print(f" - {f['command']} (ключове слово: '{f['keyword']}'{delay_info}{song_info}, пріоритет: {f['priority']})")
        else:
            print(" Команд не знайдено.")

        return result

    def execute_commands(self, found):
        found_sorted = sorted(found, key=lambda f: f["priority"], reverse=True)

        print("\n Виконання команд за пріоритетом:")
        for f in found_sorted:
            delay = f["delay"]
            cmd = f["command"]
            if delay > 0:
                print(f"⏳ Очікую {delay} сек перед виконанням '{cmd}' (пріоритет {f['priority']})...")
                time.sleep(delay)
            print(f"→ Виконую {cmd} (пріоритет {f['priority']})...")
            if cmd == "open_browser":
                print(" Відкриваю браузер...")
            elif cmd == "play_music":
                if f.get("song"):
                    print(f" Вмикаю пісню: 🎵 '{f['song']}'")
                else:
                    print(" Вмикаю музику (пісня не вказана)...")
            elif cmd == "time":
                print(" Поточний час:", datetime.now().strftime("%H:%M"))
            elif cmd == "weather":
                print(" Показую прогноз погоди...")
            elif cmd == "shutdown":
                print(" Завершення роботи системи...")
            elif cmd == "youtube":
                print(" Відкриваю YouTube...")
            else:
                print(" Невідома команда.")
            time.sleep(1)

    def __init__(self, text):
        cmds = self.recognize_commands(text)
        self.execute_commands(cmds)

#Jarvis("АТАС включи музику shape of you потім через 5 секунд через 2 хвилини вимкни комп'ютер відкрий браузер потім покажи погоду і відкрий танки ")