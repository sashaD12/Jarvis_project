import tkinter as tk
import time
import threading
import random
from datetime import datetime

import tkinter as tk
import threading
import random
import time
from datetime import datetime


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

        animate_dots()

    # === Запуск ===
    def start(self):
        threading.Thread(target=self.boot_sequence, daemon=True).start()


# === Тестовый запуск ===
if __name__ == "__main__":
    root = tk.Tk()
    app = BootScreen(root)
    app.start()
    root.mainloop()
