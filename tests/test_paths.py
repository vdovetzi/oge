import tempfile
import unittest
from pathlib import Path

from oge.paths import resolve_cli_map


class CliPathTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name) / "maps"
        self.base.mkdir()
        self.map_path = self.base / "office.yaml"
        self.map_path.write_text("image: office.pgm\n", encoding="utf-8")

    def tearDown(self):
        self.temporary.cleanup()

    def test_accepts_map_inside_invocation_directory(self):
        self.assertEqual(resolve_cli_map("office.yaml", self.base), self.map_path.resolve())

    def test_rejects_parent_traversal(self):
        outside = self.base.parent / "secret.yaml"
        outside.write_text("secret", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Access denied"):
            resolve_cli_map("../secret.yaml", self.base)

    def test_rejects_absolute_path_outside_base(self):
        outside = self.base.parent / "outside.yaml"
        outside.write_text("secret", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Access denied"):
            resolve_cli_map(outside, self.base)

    def test_rejects_symlink_escape(self):
        outside = self.base.parent / "outside.yaml"
        outside.write_text("secret", encoding="utf-8")
        (self.base / "link.yaml").symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "Access denied"):
            resolve_cli_map("link.yaml", self.base)

    def test_rejects_non_yaml_file(self):
        text_file = self.base / "notes.txt"
        text_file.write_text("text", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "extension"):
            resolve_cli_map(text_file.name, self.base)


if __name__ == "__main__":
    unittest.main()
