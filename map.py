# map_edex_fixed_optimized.py
import tkinter as tk
from tkinter import simpledialog, messagebox
from tkintermapview import TkinterMapView
import json, os, math

BG_COLOR = "#000010"
TEXT_COLOR = "#00FFCC"
FONT = ("Consolas", 12)
MARKERS_FILE = "markers.json"
SETTINGS_FILE = "map_settings.json"

def dist(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

class Tooltip(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.wm_overrideredirect(True)
        self.withdraw()
        self.label = tk.Label(self, text="", justify="left", font=("Consolas", 10),
                              bg="#ffffe0", fg="#000000", relief="solid", borderwidth=1, padx=6, pady=3)
        self.label.pack()

    def show(self, x, y, text):
        self.label.config(text=text)
        self.update_idletasks()
        self.geometry(f"+{x}+{y}")
        self.deiconify()

    def hide(self):
        self.withdraw()

class MapApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Interactive Map - eDEX Fixed")
        self.geometry("900x500")
        self.configure(bg=BG_COLOR)

        # --- map widget ---
        self.map_widget = TkinterMapView(self, width=660, height=480, corner_radius=0)
        self.map_widget.pack(side="left", fill="both", expand=False, padx=10, pady=10)
        try: self.map_widget.set_position(50.45, 30.52); self.map_widget.set_zoom(6)
        except: pass

        # --- sidebar ---
        side = tk.Frame(self, bg=BG_COLOR, width=240)
        side.pack(side="right", fill="y", padx=8, pady=8)
        tk.Label(side, text="===[ SYSTEM MAP ]===", fg=TEXT_COLOR, bg=BG_COLOR, font=("Consolas", 14)).pack(pady=6)

        self.add_btn = tk.Button(side, text="Add marker", command=self.start_adding,
                                 bg=BG_COLOR, fg=TEXT_COLOR, font=FONT, relief="flat")
        self.add_btn.pack(fill="x", pady=4)

        tk.Label(side, text="Markers:", fg=TEXT_COLOR, bg=BG_COLOR, font=("Consolas", 12)).pack(pady=(10,0), anchor="w", padx=4)
        self.listbox = tk.Listbox(side, bg="#001020", fg=TEXT_COLOR, font=FONT, activestyle="none", highlightthickness=0)
        self.listbox.pack(fill="both", expand=True, padx=4, pady=6)
        self.listbox.bind("<Double-Button-1>", self.on_listbox_double)

        btn_frame = tk.Frame(side, bg=BG_COLOR)
        btn_frame.pack(fill="x", pady=4)
        self.edit_btn = tk.Button(btn_frame, text="✏️ Edit", command=lambda: self.edit_or_delete("edit"), bg=BG_COLOR, fg=TEXT_COLOR, font=FONT, relief="flat")
        self.edit_btn.pack(side="left", fill="x", expand=True, padx=2)
        self.del_btn  = tk.Button(btn_frame, text="❌ Delete", command=lambda: self.edit_or_delete("delete"), bg=BG_COLOR, fg=TEXT_COLOR, font=FONT, relief="flat")
        self.del_btn.pack(side="left", fill="x", expand=True, padx=2)

        tk.Button(side, text="💾 Save", command=self.save_all, bg=BG_COLOR, fg=TEXT_COLOR, font=FONT, relief="flat").pack(fill="x", pady=4)
        tk.Button(side, text="📂 Load", command=self.load_all, bg=BG_COLOR, fg=TEXT_COLOR, font=FONT, relief="flat").pack(fill="x", pady=4)
        tk.Button(side, text="Clean exit", command=self.clean_exit, bg="#220000", fg="#FF6666", font=FONT, relief="flat").pack(fill="x", pady=12, side="bottom")

        self.info = tk.Label(side, text="Status: idle", fg=TEXT_COLOR, bg=BG_COLOR, font=("Consolas",10))
        self.info.pack(pady=8)

        # internal state
        self.adding = False
        self.markers = []
        self.tooltip = Tooltip(self)
        self.current_hover = None
        self.hover_threshold_px = 14

        canvas = getattr(self.map_widget, "canvas", None)
        if canvas:
            canvas.bind("<Button-1>", self._on_canvas_click, add="+")
            canvas.bind("<Motion>", self._on_canvas_motion, add="+")
            canvas.bind("<Leave>", lambda e: self.tooltip.hide(), add="+")
        else:
            self.map_widget.bind("<Button-1>", self._on_canvas_click, add="+")
            self.map_widget.bind("<Motion>", self._on_canvas_motion, add="+")

        self.load_all()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # === adding mode ===
    def start_adding(self):
        self.adding = True
        self.info.config(text="Click on the map to place marker")

    def _on_canvas_click(self, event):
        if not self.adding: return
        conv = getattr(self.map_widget, "convert_canvas_coords_to_decimal_coords", None)
        if not conv:
            messagebox.showerror("Error", "Update tkintermapview for coordinate conversion")
            self.adding = False; self.info.config(text="Status: idle"); return
        try:
            lat, lon = conv(event.x, event.y)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot get coordinates: {e}")
            self.adding = False; self.info.config(text="Status: idle"); return

        text = simpledialog.askstring("Marker text", "Enter description:", parent=self)
        if text and text.strip():
            obj = self.map_widget.set_marker(lat, lon, text=text.strip())
            self.markers.append({"lat": lat, "lon": lon, "text": text.strip(), "obj": obj})
            self.update_listbox()
            self.save_markers()
            self.info.config(text=f"Placed marker at {lat:.5f}, {lon:.5f}")
        else:
            self.info.config(text="Marker creation cancelled")
        self.adding = False

    # === hover tooltip ===
    def _on_canvas_motion(self, event):
        conv = getattr(self.map_widget, "convert_decimal_coords_to_canvas_coords", None)
        if not conv: return
        mx, my = event.x, event.y
        nearest, nearest_px = None, float('inf')
        for m in self.markers:
            try:
                cx, cy = conv(m["lat"], m["lon"])
                d = dist((mx, my), (cx, cy))
                if d < nearest_px: nearest, nearest_px = m, d
            except: continue
        if nearest and nearest_px <= self.hover_threshold_px and self.current_hover != nearest:
            self.current_hover = nearest
            self.tooltip.show(self.winfo_rootx()+mx+12, self.winfo_rooty()+my+8, nearest.get("text","(no text)"))
        elif nearest_px > self.hover_threshold_px:
            self.current_hover = None
            self.tooltip.hide()

    # === listbox double click ===
    def on_listbox_double(self, event):
        sel = self.listbox.curselection()
        if sel:
            m = self.markers[sel[0]]
            try: self.map_widget.set_position(m["lat"], m["lon"])
            except: pass

    # === edit/delete marker helper ===
    def edit_or_delete(self, action):
        sel = self.listbox.curselection()
        if not sel: messagebox.showinfo("Info", f"Select a marker to {action}"); return
        idx = sel[0]; m = self.markers[idx]
        if action == "edit":
            new_text = simpledialog.askstring("Edit marker", "New text:", initialvalue=m["text"], parent=self)
            if new_text is not None:
                m["text"] = new_text
                if m.get("obj"): m["obj"].text = new_text
                self.update_listbox(); self.save_markers()
                self.info.config(text=f"Marker {idx+1} updated")
        else:
            if messagebox.askyesno("Confirm delete", f"Delete marker #{idx+1}: {m['text']}?"):
                if m.get("obj"): m["obj"].delete()
                del self.markers[idx]; self.update_listbox(); self.save_markers()
                self.info.config(text=f"Marker {idx+1} deleted")

    # === markers load/save ===
    def save_markers(self):
        try:
            with open(MARKERS_FILE, "w", encoding="utf-8") as f:
                json.dump([{"lat":m["lat"],"lon":m["lon"],"text":m["text"]} for m in self.markers], f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot save markers: {e}")

    def load_markers(self):
        self.markers = []
        if os.path.exists(MARKERS_FILE):
            try:
                with open(MARKERS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data:
                    lat = item.get("lat") or item.get("position",[0,0])[0]
                    lon = item.get("lon") or item.get("position",[0,0])[1]
                    self.markers.append({"lat":lat, "lon":lon, "text": item.get("text",""), "obj": None})
                self.reload_markers()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load markers: {e}")

    def reload_markers(self):
        try: self.map_widget.delete_all_marker()
        except: pass
        for m in self.markers:
            try: m["obj"] = self.map_widget.set_marker(m["lat"], m["lon"], text=m["text"])
            except: m["obj"] = None
        self.update_listbox()

    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        for i, m in enumerate(self.markers):
            self.listbox.insert(tk.END, f"{i+1}: {m.get('text') or f'Marker #{i+1}'}")

    # === settings ===
    def save_settings(self):
        try:
            pos = getattr(self.map_widget, "get_position", lambda: (0,0))()
            zoom = getattr(self.map_widget, "get_zoom", lambda: 6)()
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump({"lat": pos[0], "lon": pos[1], "zoom": zoom}, f, indent=2)
        except: pass

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    d = json.load(f)
                self.map_widget.set_position(d.get("lat",50.45), d.get("lon",30.52))
                self.map_widget.set_zoom(d.get("zoom",6))
            except: pass

    def save_all(self):
        self.save_markers(); self.save_settings(); self.info.config(text="Saved.")

    def load_all(self):
        self.load_settings(); self.load_markers(); self.info.config(text="Loaded markers")

    # --- clean exit ---
    def clean_exit(self):
        if messagebox.askyesno("Clean exit", "Delete saved files and exit?"):
            for f in (MARKERS_FILE, SETTINGS_FILE):
                try: os.remove(f)
                except: pass
            self.destroy()

    def on_close(self):
        try: self.save_all()
        except: pass
        self.destroy()

if __name__ == "__main__":
    app = MapApp()
    app.mainloop()
