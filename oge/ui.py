import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .canvas import MapCanvas
from .model import OccupancyMap


class OccupancyEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Occupancy Grid Editor")
        self.geometry("1100x700")
        self.minsize(700, 450)
        self.dirty = False
        self.canvas = MapCanvas(self, self.mark_dirty, self.set_status)

        toolbar = ttk.Frame(self, padding=4)
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="Open", command=self.open_map).pack(side="left")
        ttk.Button(toolbar, text="Save", command=self.save_map).pack(side="left")
        ttk.Button(toolbar, text="Save As", command=self.save_map_as).pack(side="left")
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=6)
        ttk.Button(toolbar, text="↶", width=3, command=self.canvas.undo).pack(side="left")
        ttk.Button(toolbar, text="↷", width=3, command=self.canvas.redo).pack(side="left")
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=6)
        ttk.Button(toolbar, text="−", width=3, command=self.canvas.zoom_out).pack(side="left")
        ttk.Button(toolbar, text="+", width=3, command=self.canvas.zoom_in).pack(side="left")
        ttk.Button(toolbar, text="Fit", command=self.canvas.fit_map).pack(side="left")

        self.tool = tk.StringVar(value="Wall")
        for name in ("Wall", "Free", "Unknown"):
            button = ttk.Radiobutton(
                toolbar,
                text=name,
                value=name,
                variable=self.tool,
                command=lambda: setattr(self.canvas, "tool", self.tool.get()),
            )
            button.pack(side="left")
        ttk.Label(toolbar, text="  Size").pack(side="left")
        brush_size = ttk.Scale(
            toolbar,
            from_=1,
            to=40,
            command=lambda value: setattr(self.canvas, "brush_size", round(float(value))),
        )
        brush_size.pack(side="left")

        self.status = tk.StringVar(value="Open a YAML map to begin")
        ttk.Label(self, textvariable=self.status, padding=(8, 3)).pack(side="bottom", fill="x")
        self.canvas.pack(fill="both", expand=True)

        self.bind_all("<Control-o>", lambda _event: self.open_map())
        self.bind_all("<Control-s>", lambda _event: self.save_map())
        self.bind_all("<Control-z>", lambda _event: self.canvas.undo())
        self.bind_all("<Control-y>", lambda _event: self.canvas.redo())
        self.bind_all("<Control-Shift-Z>", lambda _event: self.canvas.redo())
        self.bind_all("<Control-plus>", lambda _event: self.canvas.zoom_in())
        self.bind_all("<Control-equal>", lambda _event: self.canvas.zoom_in())
        self.bind_all("<Control-minus>", lambda _event: self.canvas.zoom_out())
        self.bind_all("<Control-0>", lambda _event: self.canvas.fit_map())
        for key, name in (("1", "Wall"), ("2", "Free"), ("3", "Unknown")):
            self.bind_all(key, lambda _event, tool=name: self.select_tool(tool))
        self.protocol("WM_DELETE_WINDOW", self.close)

    def select_tool(self, tool):
        self.tool.set(tool)
        self.canvas.tool = tool

    def set_status(self, text):
        self.status.set(text or "Ready")

    def open_map(self):
        if not self.confirm_discard():
            return
        filename = filedialog.askopenfilename(filetypes=[("Map YAML", "*.yaml *.yml")])
        if not filename:
            return
        self.open_path(filename)

    def open_path(self, filename):
        try:
            self.canvas.set_map(OccupancyMap.load(filename))
            self.set_dirty(False)
            return True
        except (OSError, ValueError, tk.TclError) as error:
            messagebox.showerror("Cannot open map", str(error))
            return False

    def save_map(self):
        if not self.canvas.map:
            return False
        if not self.canvas.map.yaml_path:
            return self.save_map_as()
        return self.save_to(self.canvas.map.yaml_path)

    def save_map_as(self):
        if not self.canvas.map:
            return False
        filename = filedialog.asksaveasfilename(defaultextension=".yaml",
                                                filetypes=[("Map YAML", "*.yaml")])
        return self.save_to(Path(filename)) if filename else False

    def save_to(self, path):
        try:
            self.canvas.map.save(path)
            self.set_dirty(False)
            return True
        except (OSError, ValueError) as error:
            messagebox.showerror("Cannot save map", str(error))
            return False

    def mark_dirty(self):
        self.set_dirty(True)

    def set_dirty(self, dirty):
        self.dirty = dirty
        path = self.canvas.map.yaml_path if self.canvas.map else None
        name = path.name if path else "Occupancy Grid Editor"
        self.title(name + (" *" if dirty else ""))

    def confirm_discard(self):
        if not self.dirty:
            return True
        answer = messagebox.askyesnocancel("Unsaved changes", "Save changes to the current map?")
        return self.save_map() if answer is True else answer is False

    def close(self):
        if self.confirm_discard():
            self.destroy()
