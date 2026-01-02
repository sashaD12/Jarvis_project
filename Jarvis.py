import tkinter as tk
from tkinter import *
import threading
import webbrowser
import os
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import undetected_chromedriver as uc
import pyaudio
from vosk import Model, KaldiRecognizer
import json
import requests
from tkinter import messagebox
import random
from datetime import datetime
from modul_jarvis import Jarvis

driver = None
on_Jarvis = False
listening = False
stream = None

# --- Головний клас ---
class App(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resizable(False, False)
        self.title("Jarvis System")

        container = tk.Frame(self, bg="#440000")
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (JarvisPage, CipherPage, MenuPage):
            frame = F(parent=container, controller=self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("MenuPage")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

class BootScreen:
    def __init__(self, master: tk.Tk):
        self.master = master
        self.BG_COLOR = "#000010"
        self.TEXT_COLOR = "#00FFCC"
        self.FONT = ("Consolas", 13)
        self.update_time_active = False

        # === Окно ===
        self.master.title("System Boot - eDEX Style")
        self.master.geometry("1000x600")
        self.master.configure(bg=self.BG_COLOR)
        self.master.resizable(False, False)

        # === Текстовое поле ===
        self.text = tk.Text(
            self.master,
            bg=self.BG_COLOR,
            fg=self.TEXT_COLOR,
            font=self.FONT,
            bd=0,
            highlightthickness=0,
            insertbackground=self.TEXT_COLOR,
        )
        self.text.pack(fill="both", expand=True)
        self.text.insert("end", ">>> Boot sequence initiated...\n")
        self.text.config(state="disabled")

        # === Лог загрузки ===
        self.boot_lines = [
            "[BOOT] Initializing quantum core modules...",
            "[SYS] BIOS integrity: OK",
            "[KERNEL] Starting hyperthreaded virtual CPU...",
            "[SYS] Detecting hardware interfaces...",
            "[DEV] GPU: Neural Acceleration Unit [OK]",
            "[NET] Establishing secure uplink...",
            "[SEC] Checking encryption layers...",
            "[OK] Security protocol AES-4096 active",
            "[DRV] Mounting local drive /dev/sda1...",
            "[MEM] Allocating 512MB temporary cache...",
            "[AI] Loading R.I.A.T. tactical assistant...",
            "[AI] Neural links verified.",
            "[SYS] Initializing graphical layer...",
            "[APP] Loading interface elements...",
            "[SYS] Calibrating optical sensors...",
            "[SYS] Synchronizing system clock...",
            "[INFO] System Time: INIT / Galactic Cycle 000.0",
            "[SYS] Executing boot scripts...",
            "[OK] All systems operational.",
            "[LOGIN] Welcome, Colonel.",
            "[LOGIN] Loading secure environment...",
        ]

    # === Безопасный вывод текста ===
    def type_text(self, line, delay=0.015):
        self.text.config(state="normal")
        for char in line:
            self.text.insert("end", char)
            self.text.see("end")
            self.master.update()
            time.sleep(delay)
        self.text.insert("end", "\n")
        self.text.config(state="disabled")
        self.master.update()

    # === Обновление времени ===
    def update_time(self):
        if not self.update_time_active:
            return
        try:
            self.text.config(state="normal")
            all_text = self.text.get("1.0", "end").split("\n")
            new_lines = []
            for line in all_text:
                if line.startswith("[INFO] System Time:"):
                    now = datetime.now().strftime("%H:%M:%S")
                    line = f"[INFO] System Time: {now} / Galactic Cycle {random.uniform(100, 999):.1f}"
                new_lines.append(line)
            self.text.delete("1.0", "end")
            self.text.insert("end", "\n".join(new_lines))
            self.text.config(state="disabled")
        except tk.TclError:
            return
        self.master.after(1000, self.update_time)

    # === Первая стадия — загрузка ===
    def boot_sequence(self):
        for line in self.boot_lines:
            self.type_text(line, delay=random.uniform(0.005, 0.02))
            time.sleep(random.uniform(0.1, 0.3))

        self.type_text("\n>>> SYSTEM ONLINE")
        self.type_text(">>> Press ENTER to continue...", delay=0.03)

        self.update_time_active = True
        self.update_time()
        self.listen_enter_first()

    def listen_enter_first(self):
        self.master.bind("<Return>", lambda e: self.start_progress_screen())

    # === Вторая стадия — прогресс ===
    def start_progress_screen(self):
        self.update_time_active = False
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.config(state="disabled")

        self.type_text("[SYSTEM] Initializing full system...", 0.02)
        self.type_text("[PROGRESS] Loading modules: 0%", 0.02)

        hang_point = random.randint(40, 60)
        spinner = ['|', '/', '—', '\\']

        for i in range(1, 101):
            time.sleep(0.05)
            if i == hang_point:
                for _ in range(10):
                    for s in spinner:
                        self.text.config(state="normal")
                        lines = self.text.get("1.0", "end").split("\n")
                        if len(lines) >= 2:
                            lines[1] = f"[PROGRESS] Loading modules: {i}% {s}"
                            self.text.delete("2.0", "2.end")
                            self.text.insert("2.0", lines[1])
                        self.text.config(state="disabled")
                        self.text.update()
                        time.sleep(0.1)

            self.text.config(state="normal")
            lines = self.text.get("1.0", "end").split("\n")
            if len(lines) >= 2:
                lines[1] = f"[PROGRESS] Loading modules: {i}%"
                self.text.delete("2.0", "2.end")
                self.text.insert("2.0", lines[1])
            self.text.config(state="disabled")
            self.master.update()

        self.type_text("\n>>> SYSTEM FULLY LOADED")
        self.type_text(">>> Press ENTER to continue...", delay=0.03)
        self.listen_enter_second()

    def listen_enter_second(self):
        self.master.bind("<Return>", lambda e: self.start_intro())

    # === Эффект Matrix Rain и логотип ===
    def start_intro(self):
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.config(state="disabled")

        canvas = tk.Canvas(self.master, bg=self.BG_COLOR, highlightthickness=0)
        canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        width, height = 1000, 600
        columns = int(width / 10)
        drops = [random.randint(0, height // 15) for _ in range(columns)]
        symbols = "01"
        start_time = time.time()

        def draw_rain():
            elapsed = time.time() - start_time
            canvas.delete("all")
            for i in range(columns):
                for _ in range(random.randint(1, 3)):
                    char = random.choice(symbols)
                    x = i * 10
                    y = (drops[i] + random.randint(-1, 3)) * 15
                    color = self.TEXT_COLOR
                    canvas.create_text(x, y, text=char, fill=color, font=self.FONT)
                drops[i] = 0 if y > height and random.random() > 0.975 else drops[i] + 1

            if elapsed < 2:
                self.master.after(25, draw_rain)
            else:
                fade_out(0)

        def fade_out(step):
            fade_steps = 20
            alpha = 1 - step / fade_steps
            canvas.delete("all")
            for i in range(columns):
                char = random.choice(symbols)
                x = i * 10
                y = drops[i] * 15
                color = f"#{int(0*alpha):02x}{int(255*alpha):02x}{int(204*alpha):02x}"
                canvas.create_text(x, y, text=char, fill=color, font=self.FONT)
            if step < fade_steps:
                self.master.after(30, lambda: fade_out(step + 1))
            else:
                canvas.destroy()
                self.draw_logo()

        draw_rain()

    # === Отдельный метод логотипа ===
    def draw_logo(self):
        logo_lines = [
            "   _____  _____  __    __  _____  _   _ ",
            "  / ____||  __ \\|  \\  /  ||  __ \\| \\ | |",
            " | |  __ | |  | |   \\/   || |  | |  \\| |",
            " | | |_ || |  | | |\\  /| || |  | | . ` |",
            " | |__| || |__| | | \\/ | || |__| | |\\  |",
            "  \\_____||_____/|_|    |_||_____/|_| \\_|",
            "                                        ",
            "    WELCOME TO R.I.A.T. SPECIAL SYSTEM"
        ]

        self.text.tag_configure("center", justify="center")

        # отступ вниз
        for _ in range(5):
            self.text.config(state="normal")
            self.text.insert("end", "\n")
            self.text.config(state="disabled")

        for _ in logo_lines:
            self.text.config(state="normal")
            self.text.insert("end", " " * max(len(line) for line in logo_lines) + "\n", "center")
            self.text.config(state="disabled")

        positions = []
        for row, line in enumerate(logo_lines):
            for col, char in enumerate(line):
                positions.append((row + 5, col, char))
        random.shuffle(positions)

        for row, col, char in positions:
            self.text.config(state="normal")
            current_line = self.text.get(f"{row+1}.0", f"{row+1}.end")
            new_line = current_line.ljust(col)[:col] + char + current_line[col+1:]
            self.text.delete(f"{row+1}.0", f"{row+1}.end")
            self.text.insert(f"{row+1}.0", new_line, "center")
            self.text.config(state="disabled")
            self.master.update()
            time.sleep(0.002)

        self.text.config(state="normal")
        self.text.insert("end", "\n>>> Initializing", "center")
        self.text.config(state="disabled")

        dots = ["", ".", "..", "..."]
        start = time.time()

        def animate_dots(i=0):
            elapsed = time.time() - start
            self.text.config(state="normal")
            line = f">>> Initializing{dots[i % 4]}"
            last_line = self.text.index("end-1c linestart")
            self.text.delete(last_line, "end-1c")
            self.text.insert("end", line, "center")
            self.text.config(state="disabled")
            self.text.update()
            if elapsed < 10:
                self.master.after(300, lambda: animate_dots(i + 1))
            else:
                self.master.destroy()
                start_rial()

        animate_dots()

    # === Запуск ===
    def start(self):
        threading.Thread(target=self.boot_sequence, daemon=True).start()

def start_rial():
    app = App()
    app.mainloop()

# --- Сторінка Jarvis ---
class JarvisPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#440000")
        self.controller = controller
        self.create_widgets()

    def create_widgets(self):
        canvas = tk.Canvas(self, width=900, height=500, bg="#440000", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        self.start = tk.Button(self, text="Start Jarvis", bg="#000000", fg="#800000",
                  activebackground="#580101", activeforeground="#800000", command=self.start_stop)
        self.start.place(x=50, y=370)

        self.mic_btn = tk.Button(self, text="🎤 Ввімкнути", command=self.start_listening, bg="#111111", fg="white")
        self.mic_btn.place(x=50, y=430)

        self.check = tk.Text(self, height=1, width=50)
        self.check.place(x=50, y=400)

        self.btn = tk.Button(self, text="Зчитати", command=self.get_text)
        self.btn.place(x=470, y=395)

        # --- Кнопка меню ---
        tk.Button(self, text="🏠 Меню", bg="#222", fg="white",
                  command=lambda: self.controller.show_frame("MenuPage")).place(x=820, y=40)

    # --- Функціонал Jarvis ---
    def get_text(self):
        global driver, on_Jarvis
        text = self.check.get("1.0", tk.END).strip().lower()
        Jarvis(text)

    def start_stop(self):
        global on_Jarvis
        on_Jarvis = not on_Jarvis

    def start_listening(self):
        global listening, stream
        if listening:
            listening = False
            try:
                if stream:
                    stream.stop_stream()
                    stream.close()
            except:
                pass
            self.mic_btn.config(text="🎤 Ввімкнути")
            return

        def listen():
            global listening, stream
            #model_path = r"C:\Users\apple_man\Desktop\Jarvis_project\model\vosk-model-uk-v3"
            if not os.path.exists(model_path):
                print("❗ Модель не знайдено.")
                return
            model = Model(model_path)
            recognizer = KaldiRecognizer(model, 16000)
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
            stream.start_stream()
            listening = True
            self.after(0, lambda: self.mic_btn.config(text="🛑 Зупинити"))
            print("🎤 Слухаю...")

            result_text = ""
            while listening:
                data = stream.read(4000, exception_on_overflow=False)
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    result_text = result.get("text", "")
                    break
            stream.stop_stream()
            stream.close()
            p.terminate()
            listening = False
            self.after(0, lambda: self.mic_btn.config(text="🎤 Ввімкнути"))
            if result_text.strip():
                self.after(0, lambda: self.check.delete("1.0", tk.END))
                self.after(0, lambda: self.check.insert(tk.END, result_text))
                self.after(0, self.get_text)

        threading.Thread(target=listen).start()


class CipherPage(tk.Frame):
    b = 5
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#003333")
        self.controller = controller

        self.alfabet = "абвгґдеєжзиіїйклмнопрстуфхцчшщьюя"
        self.keyplus = 5
        self.keyminus = self.find_inverse(self.keyplus, len(self.alfabet))

        # Головний лівий контейнер
        left_frame = tk.Frame(self, bg="#003333")
        left_frame.pack(side="left", fill="y", padx=40, pady=40)

        tk.Label(left_frame, text="Шифратор / Дешифратор", fg="white", bg="#003333",
                 font=("Arial", 16, "bold")).pack(pady=10, anchor="w")

        key_frame = tk.Frame(left_frame, bg="#003333")
        key_frame.pack(pady=5, anchor="w")
        self.key_label = tk.Label(key_frame, text=self.get_key_text(), fg="yellow", bg="#003333",
                                  font=("Consolas", 12, "bold"))
        self.key_label.pack(side="left", padx=10)
        tk.Button(key_frame, text="➕", command=self.increase_key, bg="#006600", fg="white", width=3).pack(side="left", padx=2)
        tk.Button(key_frame, text="➖", command=self.decrease_key, bg="#660000", fg="white", width=3).pack(side="left", padx=2)

        self.mode = tk.StringVar(value="encode")
        tk.Radiobutton(left_frame, text="🔐 Зашифрувати", variable=self.mode, value="encode",
                       bg="#003333", fg="white", selectcolor="#002222").pack(anchor="w")
        tk.Radiobutton(left_frame, text="🔓 Розшифрувати", variable=self.mode, value="decode",
                       bg="#003333", fg="white", selectcolor="#002222").pack(anchor="w")

        self.input_text = tk.Text(left_frame, height=4, width=60)
        self.input_text.pack(pady=10, anchor="w")
        tk.Button(left_frame, text="▶ Виконати", command=self.process_text,
                  bg="#006666", fg="white", activebackground="#00aaaa").pack(anchor="w")
        tk.Label(left_frame, text="Результат:", fg="white", bg="#003333").pack(pady=(10, 0), anchor="w")
        self.output_text = tk.Text(left_frame, height=4, width=60, bg="#001f1f", fg="lime")
        self.output_text.pack(pady=5, anchor="w")

        # --- 🔹 ТРЕТЯ ФУНКЦІЯ: Відновлення шифру ---
        tk.Label(left_frame, text="Введіть 4 числа через пробіл:", fg="white", bg="#003333").pack(pady=(20, 5), anchor="w")
        self.recover_entry = tk.Entry(left_frame, width=40)
        self.recover_entry.pack(anchor="w")
        tk.Button(left_frame, text="🔍 Відновити шифр", command=self.recover_cipher,
                  bg="#444444", fg="white", activebackground="#777777").pack(pady=5, anchor="w")

        # --- Кнопка меню справа ---
        tk.Button(self, text="🏠 Меню", bg="#222", fg="white",
                  command=lambda: self.controller.show_frame("MenuPage")).place(relx=0.95, rely=0.05, anchor="ne")

    # --- Допоміжні функції ---
    def find_inverse(self, key, mod):
        for i in range(1, mod):
            if (key * i) % mod == 1:
                return i
        return None

    def get_key_text(self):
        return f"keyplus = {self.keyplus}   keyminus = {self.keyminus or '—'}"

    def update_key_label(self):
        self.key_label.config(text=self.get_key_text())

    def increase_key(self):
        self.keyplus = ((self.keyplus + 1)) % len(self.alfabet)
        if self.keyplus == 0:
            self.keyplus = 1
        self.keyminus = self.find_inverse(self.keyplus, len(self.alfabet))
        self.update_key_label()

    def decrease_key(self):
        self.keyplus = ((self.keyplus - 1)) % len(self.alfabet)
        if self.keyplus == 0:
            self.keyplus = len(self.alfabet) - 1
        self.keyminus = self.find_inverse(self.keyplus, len(self.alfabet))
        self.update_key_label()

    # --- 1️⃣ Шифрування / розшифрування ---
    def process_text(self):
        text = self.input_text.get("1.0", tk.END).strip().lower()
        self.output_text.delete("1.0", tk.END)
        result = ""
        mod = len(self.alfabet)
        mode = self.mode.get()
        for char in text:
            if char in self.alfabet:
                idx = self.alfabet.index(char)
                if mode == "encode":
                    new_idx = ((idx * self.keyplus) + self.b) % mod
                else:
                    if not self.keyminus:
                        result = "❌ Цей keyplus не має оберненого числа!"
                        break
                    new_idx = ((idx - self.b) * self.keyminus) % mod
                result += self.alfabet[new_idx]
            else:
                result += char
        self.output_text.insert(tk.END, result)

    # --- 2️⃣ 🔍 Відновлення шифру (нова функція) ---
    def recover_cipher(self):
        data = self.recover_entry.get().strip().split()
        if len(data) != 4:
            messagebox.showerror("Помилка", "Потрібно ввести рівно 4 числа через пробіл!")
            return

        try:
            l = [int(i) for i in data]
        except ValueError:
            messagebox.showerror("Помилка", "Введення має містити лише числа!")
            return

        if l[0] < l[1]:
            a = l[1] - l[0]
            b = l[3] - l[2]
        else:
            a = l[0] - l[1]
            b = l[2] - l[3]

        k = None
        for i in range(1, 33):
            if (a * i) % 33 == b % 33:
                k = i
                break

        t = None
        if k is not None:
            for i in range(1, 33):
                if (l[0] * k + i) % 33 == l[2] % 33:
                    t = i
                    break

        if k is not None and t is not None:
            messagebox.showinfo("Відновлений шифр", f"Відновлений шифр:\na = b*{k} + {t} (mod 33)")
        else:
            messagebox.showwarning("Результат", "Не вдалося знайти параметри шифру.")


# --- Сторінка Меню ---
# Твой API-ключ от NewsAPI.org (зарегистрируйся, получи ключ)
NEWS_API_URL = ('https://newsapi.org/v2/everything?'
       'language=ru&'
       'country=ua&'
       'apiKey=984a385872e24689b1f01ad8fc9d1167')

class MenuPage(tk.Frame):
    NEWS_API_URL = ('https://newsapi.org/v2/top-headlines?category=business&apiKey=984a385872e24689b1f01ad8fc9d1167')
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#584C01")
        self.controller = controller

        left_menu = tk.Frame(self, bg="#584C01")
        left_menu.pack(side="left", fill="y", padx=20, pady=20)

        tk.Label(left_menu, text="Меню", bg="#584C01", fg="white",
                 font=("Helvetica", 20, "bold")).pack(pady=(0,20), anchor="w")

        tk.Button(left_menu, text="🤖 Jarvis", width=20, height=2,
                  command=lambda: controller.show_frame("JarvisPage")).pack(pady=5, anchor="w")
        tk.Button(left_menu, text="🧩 Cipher Tool", width=20, height=2,
                  command=lambda: controller.show_frame("CipherPage")).pack(pady=5, anchor="w")
        tk.Button(left_menu, text="🚪 Вийти", width=20, height=2,
                  command=controller.destroy).pack(pady=20, anchor="w")

        # Правая часть — новости
        right_frame = tk.Frame(self, bg="#584C01")
        right_frame.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        tk.Label(right_frame, text="📢 Главные новости:", bg="#584C01", fg="white",
                 font=("Arial", 16, "bold")).pack(anchor="nw")

        self.news_text = tk.Text(right_frame, bg="#403000", fg="white", wrap="word")
        self.news_text.pack(fill="both", expand=True, pady=10)

        # Загрузка новостей
        self.load_news()

    def load_news(self):
        self.news_text.delete("1.0", tk.END)
        try:
            resp = requests.get(self.NEWS_API_URL, timeout=5)
            data = resp.json()
            articles = data.get("articles", [])
        except Exception as e:
            self.news_text.insert(tk.END, "Ошибка загрузки новостей:\n" + str(e))
            return

        if not articles:
            self.news_text.insert(tk.END, "Нет новостей.")
            return

        # Показать первые 5 новостей
        for i, art in enumerate(articles[:]):
            title = art.get("title", "Без заголовка")
            desc = art.get("description", "")
            self.news_text.insert(tk.END, f"{i+1}. {title}\n{desc}\n\n")


# --- Запуск ---
if __name__ == "__main__":
    root = tk.Tk()
    app = BootScreen(root)
    app.start()
    root.mainloop()

