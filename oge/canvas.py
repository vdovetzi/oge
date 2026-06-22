import math
import tkinter as tk


class MapCanvas(tk.Canvas):
    ZOOM_LEVELS = (0.125, 0.25, 0.5, 1, 2, 4, 8, 16, 32)
    HISTORY_LIMIT = 30
    HISTORY_BYTES = 128 * 1024 * 1024

    def __init__(self, master, on_modified, on_cursor):
        super().__init__(master, background="#202124", highlightthickness=0)
        self.map = None
        self.on_modified = on_modified
        self.on_cursor = on_cursor
        self.tool = "Wall"
        self.brush_size = 1
        self.zoom_index = 3
        self.pan_x = self.pan_y = 20.0
        self.last_cell = self.last_mouse = None
        self.drawing = self.panning = False
        self.stroke_before = None
        self.undo_stack = []
        self.redo_stack = []
        self.render_left = self.render_top = 0
        self.render_pending = False
        self.fit_pending = False
        self.photo = self.base_photo = None
        self.image_item = self.create_image(0, 0, anchor="nw")
        self.cursor_item = self.create_rectangle(0, 0, 0, 0, state="hidden")
        self.bind("<ButtonPress-1>", self.mouse_down)
        self.bind("<B1-Motion>", self.mouse_move)
        self.bind("<ButtonRelease-1>", self.mouse_up)
        self.bind("<ButtonPress-2>", self.start_pan)
        self.bind("<B2-Motion>", self.pan_move)
        self.bind("<ButtonRelease-2>", self.stop_pan)
        self.bind("<Motion>", self.mouse_move)
        self.bind("<Leave>", lambda _event: self.hide_cursor())
        self.bind("<MouseWheel>", self.mouse_wheel)
        self.bind("<Button-4>", lambda event: self.zoom_in(event.x, event.y))
        self.bind("<Button-5>", lambda event: self.zoom_out(event.x, event.y))
        self.bind("<Configure>", self.resized)

    @property
    def scale(self):
        return self.ZOOM_LEVELS[self.zoom_index]

    def set_map(self, occupancy_map):
        self.map = occupancy_map
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.zoom_index = 3
        if self.winfo_width() > 10 and self.winfo_height() > 10:
            self.fit_pending = False
            self.fit_map()
        else:
            self.fit_pending = True
            self.schedule_render()

    def resized(self, event):
        if self.fit_pending and event.width > 10 and event.height > 10:
            self.fit_pending = False
            self.fit_map()
        else:
            self.schedule_render()

    def render(self):
        if not self.map:
            return
        canvas_width = max(1, self.winfo_width())
        canvas_height = max(1, self.winfo_height())
        left = max(0, math.floor(-self.pan_x / self.scale))
        right = min(self.map.width, math.ceil((canvas_width - self.pan_x) / self.scale))
        top = max(0, math.floor(-self.pan_y / self.scale))
        bottom = min(self.map.height, math.ceil((canvas_height - self.pan_y) / self.scale))

        if self.scale < 1:
            factor = int(round(1 / self.scale))
            left = left // factor * factor
            top = top // factor * factor
        if right <= left or bottom <= top:
            self.itemconfigure(self.image_item, state="hidden")
            self.redraw_overlay()
            return

        rows = []
        if self.scale < 1:
            output_width = math.ceil((right - left) / factor)
            output_height = math.ceil((bottom - top) / factor)
            for y in range(top, bottom, factor):
                start = y * self.map.width + left
                rows.append(self.map.pixels[start:y * self.map.width + right:factor])
        else:
            output_width = right - left
            output_height = bottom - top
            for y in range(top, bottom):
                start = y * self.map.width + left
                rows.append(self.map.pixels[start:start + output_width])
        pgm = f"P5\n{output_width} {output_height}\n255\n".encode() + b"".join(rows)
        self.base_photo = tk.PhotoImage(data=pgm, format="PPM")
        if self.scale >= 1:
            factor = int(self.scale)
            self.photo = self.base_photo.zoom(factor, factor)
        else:
            self.photo = self.base_photo
        self.render_left, self.render_top = left, top
        self.itemconfigure(self.image_item, image=self.photo, state="normal")
        self.coords(self.image_item,
                    self.pan_x + left * self.scale,
                    self.pan_y + top * self.scale)
        self.redraw_overlay()

    def schedule_render(self):
        if self.render_pending:
            return
        self.render_pending = True
        self.after_idle(self.finish_render)

    def finish_render(self):
        self.render_pending = False
        self.render()

    def redraw_overlay(self):
        self.delete("grid")
        if not self.map:
            return
        if self.scale >= 8:
            left = max(0, int(-self.pan_x / self.scale))
            right = min(self.map.width, math.ceil((self.winfo_width() - self.pan_x) / self.scale))
            top = max(0, int(-self.pan_y / self.scale))
            bottom = min(
                self.map.height,
                math.ceil((self.winfo_height() - self.pan_y) / self.scale),
            )
            for x in range(left, right + 1):
                px = self.pan_x + x * self.scale
                self.create_line(px, self.pan_y + top * self.scale,
                                 px, self.pan_y + bottom * self.scale,
                                 fill="#303236", tags="grid")
            for y in range(top, bottom + 1):
                py = self.pan_y + y * self.scale
                self.create_line(self.pan_x + left * self.scale, py,
                                 self.pan_x + right * self.scale, py,
                                 fill="#303236", tags="grid")
        self.tag_raise(self.cursor_item)

    def cell_at(self, x, y):
        if not self.map:
            return None
        cell = (math.floor((x - self.pan_x) / self.scale),
                math.floor((y - self.pan_y) / self.scale))
        return cell if 0 <= cell[0] < self.map.width and 0 <= cell[1] < self.map.height else None

    def brush_value(self):
        negate = self.map.metadata.negate
        if self.tool == "Wall":
            return 255 if negate else 0
        if self.tool == "Free":
            return 0 if negate else 254
        return 50 if negate else 205

    def draw_at(self, cell):
        if cell is None:
            return
        cx, cy = cell
        radius = self.brush_size / 2
        value = self.brush_value()
        if self.brush_size == 1:
            self.map.pixels[cy * self.map.width + cx] = value
        else:
            top = max(0, int(cy - radius))
            bottom = min(self.map.height - 1, int(cy + radius))
            left = max(0, int(cx - radius))
            right = min(self.map.width - 1, int(cx + radius))
            for y in range(top, bottom + 1):
                for x in range(left, right + 1):
                    if (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2:
                        self.map.pixels[y * self.map.width + x] = value
        self.last_cell = cell

    def draw_line_to(self, cell):
        if cell is None or self.last_cell is None:
            return
        x, y = self.last_cell
        end_x, end_y = cell
        dx, sx = abs(end_x - x), 1 if x < end_x else -1
        dy, sy = -abs(end_y - y), 1 if y < end_y else -1
        error = dx + dy
        while True:
            self.draw_at((x, y))
            if (x, y) == cell:
                break
            twice = 2 * error
            if twice >= dy:
                error += dy
                x += sx
            if twice <= dx:
                error += dx
                y += sy
        self.on_modified()
        self.schedule_render()

    def mouse_down(self, event):
        if event.state & 0x0004:
            self.start_pan(event)
        else:
            self.drawing = True
            self.stroke_before = bytes(self.map.pixels) if self.map else None
            self.draw_at(self.cell_at(event.x, event.y))
            self.on_modified()
            self.schedule_render()

    def mouse_move(self, event):
        if self.panning:
            self.pan_move(event)
        elif self.drawing:
            self.draw_line_to(self.cell_at(event.x, event.y))
        self.show_cursor(event.x, event.y)

    def mouse_up(self, _event):
        self.drawing = False
        self.last_cell = None
        if self.map and self.stroke_before is not None and self.stroke_before != self.map.pixels:
            self.undo_stack.append(self.stroke_before)
            self.trim_history(self.undo_stack)
            self.redo_stack.clear()
        self.stroke_before = None
        self.stop_pan()

    def undo(self):
        if not self.map or not self.undo_stack:
            return
        self.redo_stack.append(bytes(self.map.pixels))
        self.trim_history(self.redo_stack)
        self.map.pixels[:] = self.undo_stack.pop()
        self.on_modified()
        self.render()

    def redo(self):
        if not self.map or not self.redo_stack:
            return
        self.undo_stack.append(bytes(self.map.pixels))
        self.trim_history(self.undo_stack)
        self.map.pixels[:] = self.redo_stack.pop()
        self.on_modified()
        self.render()

    def trim_history(self, history):
        while len(history) > self.HISTORY_LIMIT:
            history.pop(0)
        while len(history) > 1 and sum(map(len, history)) > self.HISTORY_BYTES:
            history.pop(0)

    def start_pan(self, event):
        self.panning = True
        self.last_mouse = (event.x, event.y)
        self.configure(cursor="fleur")

    def pan_move(self, event):
        if not self.panning:
            return
        self.pan_x += event.x - self.last_mouse[0]
        self.pan_y += event.y - self.last_mouse[1]
        self.last_mouse = (event.x, event.y)
        self.coords(self.image_item,
                    self.pan_x + self.render_left * self.scale,
                    self.pan_y + self.render_top * self.scale)
        self.redraw_overlay()
        self.schedule_render()

    def stop_pan(self, _event=None):
        self.panning = False
        self.configure(cursor="")

    def show_cursor(self, x, y):
        cell = self.cell_at(x, y)
        if cell is None:
            self.hide_cursor()
            return
        cx, cy = cell
        radius = self.brush_size / 2
        if self.brush_size == 1:
            x1, y1 = self.pan_x + cx * self.scale, self.pan_y + cy * self.scale
            x2, y2 = x1 + self.scale, y1 + self.scale
        else:
            x1 = self.pan_x + (cx + 0.5 - radius) * self.scale
            y1 = self.pan_y + (cy + 0.5 - radius) * self.scale
            x2 = self.pan_x + (cx + 0.5 + radius) * self.scale
            y2 = self.pan_y + (cy + 0.5 + radius) * self.scale
        self.coords(self.cursor_item, x1, y1, x2, y2)
        self.itemconfigure(self.cursor_item, state="normal", outline="#2f8bd8", width=2)
        map_y = self.map.height - cy - 1
        meta = self.map.metadata
        world_x = meta.origin_x + (cx + 0.5) * meta.resolution
        world_y = meta.origin_y + (map_y + 0.5) * meta.resolution
        self.on_cursor(f"Cell {cx}, {map_y}    World {world_x:.3f}, {world_y:.3f} m")

    def hide_cursor(self):
        self.itemconfigure(self.cursor_item, state="hidden")
        self.on_cursor("")

    def mouse_wheel(self, event):
        (self.zoom_in if event.delta > 0 else self.zoom_out)(event.x, event.y)

    def set_zoom(self, index, anchor_x=None, anchor_y=None):
        if not self.map:
            return
        index = max(0, min(len(self.ZOOM_LEVELS) - 1, index))
        if index == self.zoom_index:
            return
        anchor_x = self.winfo_width() / 2 if anchor_x is None else anchor_x
        anchor_y = self.winfo_height() / 2 if anchor_y is None else anchor_y
        map_x = (anchor_x - self.pan_x) / self.scale
        map_y = (anchor_y - self.pan_y) / self.scale
        self.zoom_index = index
        self.pan_x = anchor_x - map_x * self.scale
        self.pan_y = anchor_y - map_y * self.scale
        self.render()

    def zoom_in(self, x=None, y=None):
        self.set_zoom(self.zoom_index + 1, x, y)

    def zoom_out(self, x=None, y=None):
        self.set_zoom(self.zoom_index - 1, x, y)

    def fit_map(self):
        if not self.map:
            return
        available = min(max(1, self.winfo_width() - 40) / self.map.width,
                        max(1, self.winfo_height() - 40) / self.map.height)
        fitting = [i for i, level in enumerate(self.ZOOM_LEVELS) if level <= available]
        self.zoom_index = fitting[-1] if fitting else 0
        self.pan_x = (self.winfo_width() - self.map.width * self.scale) / 2
        self.pan_y = (self.winfo_height() - self.map.height * self.scale) / 2
        self.render()
