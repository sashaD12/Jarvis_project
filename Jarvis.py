import tkinter as tk
from tkinter import messagebox
import threading
from modul_jarvis import Jarvis
from backend_cipher import CipherBackend
from backend_news import NewsBackend
from microphone_capture import capture_text_from_microphone
from map import MapPage

on_Jarvis = False
listening = False


class App(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resizable(False, False)
        self.title("Jarvis System")
        self.geometry("900x500")

        container = tk.Frame(self, bg="#440000")
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (JarvisPage, CipherPage, MapPage, MenuPage):
            frame = F(parent=container, controller=self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("MenuPage")

    def show_frame(self, page_name: str) -> None:
        frame = self.frames[page_name]
        frame.tkraise()


def start_rial() -> None:
    app = App()
    app.mainloop()


class JarvisPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#440000")
        self.controller = controller
        self.listen_stop = False
        self.listen_thread: threading.Thread | None = None
        self.create_widgets()

    def create_widgets(self) -> None:
        canvas = tk.Canvas(self, width=900, height=500, bg="#440000", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        self.start = tk.Button(
            self,
            text="Start Jarvis: OFF",
            bg="#000000",
            fg="#800000",
            activebackground="#580101",
            activeforeground="#800000",
            command=self.start_stop,
        )
        self.start.place(x=50, y=340)

        self.mic_btn = tk.Button(
            self,
            text="Ввімкнути мікрофон",
            command=self.toggle_listening,
            bg="#111111",
            fg="white",
        )
        self.mic_btn.place(x=50, y=430)

        self.check = tk.Text(self, height=1, width=50)
        self.check.place(x=50, y=400)

        self.btn = tk.Button(self, text="Зчитати", command=self.get_text)
        self.btn.place(x=470, y=395)

        self.status = tk.Text(self, height=8, width=70, bg="#220000", fg="#ffaaaa")
        self.status.place(x=50, y=40)

        tk.Button(
            self,
            text="Меню",
            bg="#222",
            fg="white",
            command=lambda: self.controller.show_frame("MenuPage"),
        ).place(x=820, y=40)

    def append_status(self, message: str) -> None:
        self.status.insert(tk.END, message + "\n")
        self.status.see(tk.END)

    def set_status_threadsafe(self, message: str) -> None:
        self.after(0, lambda: self.append_status(message))

    def confirm_threadsafe(self, title: str, message: str) -> bool:
        result = {"value": False}
        done = threading.Event()

        def ask() -> None:
            result["value"] = bool(messagebox.askyesno(title, message, parent=self))
            done.set()

        self.after(0, ask)
        done.wait(timeout=120)
        return result["value"]

    def run_jarvis(self, text: str) -> None:
        global on_Jarvis
        if not on_Jarvis:
            self.append_status("Jarvis вимкнено. Натисніть Start Jarvis.")
            return
        if not text.strip():
            self.append_status("Порожній текст.")
            return

        def worker() -> None:
            Jarvis(
                text,
                status_callback=self.set_status_threadsafe,
                confirm_callback=self.confirm_threadsafe,
                execute=True,
            )

        threading.Thread(target=worker, daemon=True).start()

    def get_text(self) -> None:
        text = self.check.get("1.0", tk.END).strip().lower()
        self.run_jarvis(text)

    def start_stop(self) -> None:
        global on_Jarvis
        on_Jarvis = not on_Jarvis
        state = "ON" if on_Jarvis else "OFF"
        self.start.config(text=f"Start Jarvis: {state}")
        self.append_status(f"Jarvis {state}")

    def toggle_listening(self) -> None:
        global listening
        if listening:
            self.listen_stop = True
            self.append_status("Зупинка мікрофона...")
            return
        self.listen_stop = False
        listening = True
        self.mic_btn.config(text="Зупинити мікрофон")
        self.append_status("Слухаю...")
        self.listen_thread = threading.Thread(target=self._listen_worker, daemon=True)
        self.listen_thread.start()

    def _listen_worker(self) -> None:
        global listening
        try:
            result_text = capture_text_from_microphone(should_stop=lambda: self.listen_stop)
            def apply_result() -> None:
                if result_text:
                    self.check.delete("1.0", tk.END)
                    self.check.insert(tk.END, result_text)
                    self.append_status(f"Розпізнано: {result_text}")
                    self.run_jarvis(result_text)
                else:
                    self.append_status("Нічого не розпізнано.")

            self.after(0, apply_result)
        except Exception as e:
            self.after(0, lambda: self.append_status(f"Помилка розпізнавання: {e}"))
        finally:
            listening = False
            self.listen_stop = False
            self.after(0, lambda: self.mic_btn.config(text="Ввімкнути мікрофон"))
            self.after(0, lambda: self.append_status("Мікрофон зупинено."))


class CipherPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#003333")
        self.controller = controller
        self.backend = CipherBackend()

        left_frame = tk.Frame(self, bg="#003333")
        left_frame.pack(side="left", fill="y", padx=40, pady=40)

        tk.Label(
            left_frame,
            text="Шифратор / Дешифратор",
            fg="white",
            bg="#003333",
            font=("Arial", 16, "bold"),
        ).pack(pady=10, anchor="w")

        key_frame = tk.Frame(left_frame, bg="#003333")
        key_frame.pack(pady=5, anchor="w")
        self.key_label = tk.Label(
            key_frame,
            text=self.get_key_text(),
            fg="yellow",
            bg="#003333",
            font=("Consolas", 12, "bold"),
        )
        self.key_label.pack(side="left", padx=10)
        tk.Button(
            key_frame,
            text="+",
            command=self.increase_key,
            bg="#006600",
            fg="white",
            width=3,
        ).pack(side="left", padx=2)
        tk.Button(
            key_frame,
            text="-",
            command=self.decrease_key,
            bg="#660000",
            fg="white",
            width=3,
        ).pack(side="left", padx=2)

        self.mode = tk.StringVar(value="encode")
        tk.Radiobutton(
            left_frame,
            text="Зашифрувати",
            variable=self.mode,
            value="encode",
            bg="#003333",
            fg="white",
            selectcolor="#002222",
        ).pack(anchor="w")
        tk.Radiobutton(
            left_frame,
            text="Розшифрувати",
            variable=self.mode,
            value="decode",
            bg="#003333",
            fg="white",
            selectcolor="#002222",
        ).pack(anchor="w")

        self.input_text = tk.Text(left_frame, height=4, width=60)
        self.input_text.pack(pady=10, anchor="w")
        tk.Button(
            left_frame,
            text="Виконати",
            command=self.process_text,
            bg="#006666",
            fg="white",
            activebackground="#00aaaa",
        ).pack(anchor="w")
        tk.Label(left_frame, text="Результат:", fg="white", bg="#003333").pack(
            pady=(10, 0), anchor="w"
        )
        self.output_text = tk.Text(left_frame, height=4, width=60, bg="#001f1f", fg="lime")
        self.output_text.pack(pady=5, anchor="w")

        tk.Label(
            left_frame,
            text="Введіть 4 числа через пробіл:",
            fg="white",
            bg="#003333",
        ).pack(pady=(20, 5), anchor="w")
        self.recover_entry = tk.Entry(left_frame, width=40)
        self.recover_entry.pack(anchor="w")
        tk.Button(
            left_frame,
            text="Відновити шифр",
            command=self.recover_cipher,
            bg="#444444",
            fg="white",
            activebackground="#777777",
        ).pack(pady=5, anchor="w")

        tk.Button(
            self,
            text="Меню",
            bg="#222",
            fg="white",
            command=lambda: self.controller.show_frame("MenuPage"),
        ).place(relx=0.95, rely=0.05, anchor="ne")

    def get_key_text(self) -> str:
        return f"keyplus = {self.backend.keyplus}   keyminus = {self.backend.keyminus or '—'}"

    def update_key_label(self) -> None:
        self.key_label.config(text=self.get_key_text())

    def increase_key(self) -> None:
        self.backend.keyplus = (self.backend.keyplus + 1) % len(self.backend.alfabet)
        if self.backend.keyplus == 0:
            self.backend.keyplus = 1
        self.backend.keyminus = self.backend.find_inverse(
            self.backend.keyplus, len(self.backend.alfabet)
        )
        self.update_key_label()

    def decrease_key(self) -> None:
        self.backend.keyplus = (self.backend.keyplus - 1) % len(self.backend.alfabet)
        if self.backend.keyplus == 0:
            self.backend.keyplus = len(self.backend.alfabet) - 1
        self.backend.keyminus = self.backend.find_inverse(
            self.backend.keyplus, len(self.backend.alfabet)
        )
        self.update_key_label()

    def process_text(self) -> None:
        text = self.input_text.get("1.0", tk.END).strip().lower()
        self.output_text.delete("1.0", tk.END)
        result = self.backend.process_text(text, self.mode.get())
        self.output_text.insert(tk.END, result)

    def recover_cipher(self) -> None:
        data = self.recover_entry.get().strip().split()
        result = self.backend.recover_cipher(data)
        if "Помилка" in result or "Не вдалося" in result:
            messagebox.showerror("Помилка", result)
        else:
            messagebox.showinfo("Відновлений шифр", result)


class MenuPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#584C01")
        self.controller = controller

        left_menu = tk.Frame(self, bg="#584C01")
        left_menu.pack(side="left", fill="y", padx=20, pady=20)

        tk.Label(
            left_menu,
            text="Меню",
            bg="#584C01",
            fg="white",
            font=("Helvetica", 20, "bold"),
        ).pack(pady=(0, 20), anchor="w")

        tk.Button(
            left_menu,
            text="Jarvis",
            width=20,
            height=2,
            command=lambda: controller.show_frame("JarvisPage"),
        ).pack(pady=5, anchor="w")
        tk.Button(
            left_menu,
            text="Cipher Tool",
            width=20,
            height=2,
            command=lambda: controller.show_frame("CipherPage"),
        ).pack(pady=5, anchor="w")
        tk.Button(
            left_menu,
            text="Map",
            width=20,
            height=2,
            command=lambda: controller.show_frame("MapPage"),
        ).pack(pady=5, anchor="w")
        tk.Button(
            left_menu,
            text="Вийти",
            width=20,
            height=2,
            command=controller.destroy,
        ).pack(pady=20, anchor="w")

        right_frame = tk.Frame(self, bg="#584C01")
        right_frame.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        tk.Label(
            right_frame,
            text="Головні новини:",
            bg="#584C01",
            fg="white",
            font=("Arial", 16, "bold"),
        ).pack(anchor="nw")

        self.news_text = tk.Text(right_frame, bg="#403000", fg="white", wrap="word")
        self.news_text.pack(fill="both", expand=True, pady=10)

        self.load_news()

    def load_news(self) -> None:
        backend = NewsBackend()
        news = backend.fetch_news()
        self.news_text.insert(tk.END, news)


if __name__ == "__main__":
    start_rial()
