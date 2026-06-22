import tempfile
import unittest
from pathlib import Path

from oge.model import Metadata, OccupancyMap


class OccupancyMapTests(unittest.TestCase):
    def test_binary_pgm_preserves_whitespace_pixel_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "map.pgm"
            path.write_bytes(b"P5\n# comment\n2 2\n255\n" + bytes((10, 32, 0, 255)))
            width, height, pixels = OccupancyMap.read_pgm(path)
            self.assertEqual((width, height), (2, 2))
            self.assertEqual(pixels, bytes((10, 32, 0, 255)))

    def test_ascii_pgm_is_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "map.pgm"
            path.write_text("P2\n2 2\n255\n0 205 254 255\n", encoding="ascii")
            self.assertEqual(OccupancyMap.read_pgm(path), (2, 2, bytes((0, 205, 254, 255))))

    def test_map_saver_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "office.yaml"
            source = OccupancyMap(
                3,
                2,
                bytes((0, 205, 254, 10, 32, 255)),
                Metadata(0.025, -1.2, 3.4, 0.1, False, 0.7, 0.2),
            )
            source.save(path)
            loaded = OccupancyMap.load(path)
            self.assertEqual((loaded.width, loaded.height), (3, 2))
            self.assertEqual(loaded.pixels, source.pixels)
            self.assertEqual(loaded.metadata, source.metadata)
            self.assertEqual(loaded.yaml_path, path.resolve())

    def test_invalid_thresholds_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "threshold"):
            Metadata(free_threshold=0.8, occupied_threshold=0.6).validate()

    def test_truncated_pgm_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.pgm"
            path.write_bytes(b"P5\n2 2\n255\n\x00")
            with self.assertRaisesRegex(ValueError, "incomplete"):
                OccupancyMap.read_pgm(path)


if __name__ == "__main__":
    unittest.main()
