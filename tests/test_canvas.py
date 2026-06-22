import tkinter as tk
import unittest

from oge.canvas import MapCanvas
from oge.model import Metadata, OccupancyMap


def display_available():
    try:
        root = tk.Tk()
        root.destroy()
        return True
    except tk.TclError:
        return False


@unittest.skipUnless(display_available(), "Tk tests require a display")
class MapCanvasTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.geometry("640x480")
        self.modified = 0
        self.canvas = MapCanvas(self.root, self.mark_modified, lambda _text: None)
        self.canvas.pack(fill="both", expand=True)
        self.root.update()
        pixels = bytes([205]) * (100 * 100)
        self.canvas.set_map(OccupancyMap(100, 100, pixels, Metadata()))
        self.root.update()

    def tearDown(self):
        self.root.destroy()

    def mark_modified(self):
        self.modified += 1

    def test_maximum_zoom_allocates_only_visible_buffer(self):
        self.canvas.set_zoom(len(self.canvas.ZOOM_LEVELS) - 1, 320, 240)
        self.root.update()
        self.assertLessEqual(self.canvas.photo.width(), self.canvas.winfo_width() + 64)
        self.assertLessEqual(self.canvas.photo.height(), self.canvas.winfo_height() + 64)

    def test_single_cell_edit_undo_and_redo(self):
        original = bytes(self.canvas.map.pixels)
        self.canvas.tool = "Wall"
        self.canvas.stroke_before = original
        self.canvas.draw_at((7, 9))
        self.canvas.mouse_up(None)
        changed = bytes(self.canvas.map.pixels)
        self.assertNotEqual(changed, original)
        self.assertEqual(self.canvas.map.pixels[9 * 100 + 7], 0)

        self.canvas.undo()
        self.assertEqual(bytes(self.canvas.map.pixels), original)
        self.canvas.redo()
        self.assertEqual(bytes(self.canvas.map.pixels), changed)

    def test_cell_coordinates_follow_pan_and_zoom(self):
        self.canvas.pan_x = 20
        self.canvas.pan_y = 30
        self.canvas.zoom_index = 4  # 2x
        self.assertEqual(self.canvas.cell_at(27, 39), (3, 4))


if __name__ == "__main__":
    unittest.main()
