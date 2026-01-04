import tkinter as tk
from intro import BootScreen

if __name__ == "__main__":
    root = tk.Tk()
    app = BootScreen(root)
    app.start()
    root.mainloop()
