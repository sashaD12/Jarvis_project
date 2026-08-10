import os
from dotenv import load_dotenv

from config_loader import BASE_DIR

load_dotenv(os.path.join(BASE_DIR, ".env"))

import tkinter as tk
from intro import BootScreen

if __name__ == "__main__":
    root = tk.Tk()
    app = BootScreen(root)
    app.start()
    root.mainloop()
