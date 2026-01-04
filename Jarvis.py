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
from backend_cipher import CipherBackend
from backend_news import NewsBackend

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
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#003333")
        self.controller = controller
        self.backend = CipherBackend()

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

    def get_key_text(self):
        return f"keyplus = {self.backend.keyplus}   keyminus = {self.backend.keyminus or '—'}"

    def update_key_label(self):
        self.key_label.config(text=self.get_key_text())

    def increase_key(self):
        self.backend.keyplus = ((self.backend.keyplus + 1)) % len(self.backend.alfabet)
        if self.backend.keyplus == 0:
            self.backend.keyplus = 1
        self.backend.keyminus = self.backend.find_inverse(self.backend.keyplus, len(self.backend.alfabet))
        self.update_key_label()

    def decrease_key(self):
        self.backend.keyplus = ((self.backend.keyplus - 1)) % len(self.backend.alfabet)
        if self.backend.keyplus == 0:
            self.backend.keyplus = len(self.backend.alfabet) - 1
        self.backend.keyminus = self.backend.find_inverse(self.backend.keyplus, len(self.backend.alfabet))
        self.update_key_label()

    def process_text(self):
        text = self.input_text.get("1.0", tk.END).strip().lower()
        self.output_text.delete("1.0", tk.END)
        result = self.backend.process_text(text, self.mode.get())
        self.output_text.insert(tk.END, result)

    def recover_cipher(self):
        data = self.recover_entry.get().strip().split()
        result = self.backend.recover_cipher(data)
        if "Помилка" in result or "Не вдалося" in result:
            messagebox.showerror("Помилка", result)
        else:
            messagebox.showinfo("Відновлений шифр", result)


# --- Сторінка Меню ---
# Твой API-ключ от NewsAPI.org (зарегистрируйся, получи ключ)
NEWS_API_URL = ('https://newsapi.org/v2/everything?'
       'language=ru&'
       'country=ua&'
       'apiKey=984a385872e24689b1f01ad8fc9d1167')

class MenuPage(tk.Frame):
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
        backend = NewsBackend()
        news = backend.fetch_news()
        self.news_text.insert(tk.END, news)

if __name__ == "__main__":
    start_rial()