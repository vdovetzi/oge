import tempfile
import unittest
from pathlib import Path

from oge.model import Metadata, OccupancyMap
from oge.ui import OccupancyEditor
from tests.test_canvas import display_available


@unittest.skipUnless(display_available(), "Tk tests require a display")
class OccupancyEditorTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "map.yaml"
        OccupancyMap(2, 2, bytes((0, 205, 254, 255)), Metadata()).save(self.path)
        self.app = OccupancyEditor()
        self.app.update()

    def tearDown(self):
        self.app.destroy()
        self.directory.cleanup()

    def test_open_edit_and_save(self):
        self.assertTrue(self.app.open_path(self.path))
        self.assertEqual(self.app.canvas.map.width, 2)
        self.app.canvas.map.pixels[0] = 254
        self.app.mark_dirty()
        self.assertTrue(self.app.dirty)
        self.assertTrue(self.app.save_map())
        self.assertFalse(self.app.dirty)
        self.assertEqual(OccupancyMap.load(self.path).pixels[0], 254)

    def test_tool_and_status_updates(self):
        self.app.select_tool("Unknown")
        self.assertEqual(self.app.canvas.tool, "Unknown")
        self.app.set_status("Cell 1, 2")
        self.assertEqual(self.app.status.get(), "Cell 1, 2")


if __name__ == "__main__":
    unittest.main()
