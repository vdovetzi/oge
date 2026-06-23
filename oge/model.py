import math
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .paths import resolve_within


class _PgmReader:
    def __init__(self, data):
        self.data = data
        self.index = 0

    def read(self):
        magic, width, height, maximum = self.read_header()
        self.validate_header(magic, width, height, maximum)
        if magic == b"P5":
            pixels = self.read_binary_pixels(width, height)
        else:
            pixels = self.read_ascii_pixels(width, height)
        if len(pixels) != width * height:
            raise ValueError("PGM image is incomplete")
        return width, height, pixels

    def read_header(self):
        try:
            return self.token(), int(self.token()), int(self.token()), int(self.token())
        except ValueError as error:
            raise ValueError("Invalid PGM header") from error

    @staticmethod
    def validate_header(magic, width, height, maximum):
        if magic not in (b"P5", b"P2") or maximum != 255:
            raise ValueError("Only 8-bit PGM maps are supported")
        if width <= 0 or height <= 0:
            raise ValueError("PGM dimensions must be greater than zero")

    def read_binary_pixels(self, width, height):
        self.consume_raster_separator()
        return self.data[self.index:self.index + width * height]

    def read_ascii_pixels(self, width, height):
        try:
            values = [int(self.token()) for _ in range(width * height)]
        except ValueError as error:
            raise ValueError("Invalid PGM pixel data") from error
        if any(value < 0 or value > 255 for value in values):
            raise ValueError("PGM pixel value is outside 0..255")
        return bytes(values)

    def token(self):
        self.skip_whitespace_and_comments()
        start = self.index
        while self.index < len(self.data) and not self.data[self.index:self.index + 1].isspace():
            self.index += 1
        return self.data[start:self.index]

    def skip_whitespace_and_comments(self):
        while self.index < len(self.data):
            current = self.data[self.index:self.index + 1]
            if current == b"#":
                self.skip_comment()
            elif current.isspace():
                self.index += 1
            else:
                return

    def skip_comment(self):
        newline = self.data.find(b"\n", self.index)
        if newline < 0:
            raise ValueError("Invalid PGM comment")
        self.index = newline + 1

    def consume_raster_separator(self):
        if self.index >= len(self.data) or not self.data[self.index:self.index + 1].isspace():
            raise ValueError("Invalid PGM header")
        self.index += 2 if self.data[self.index:self.index + 2] == b"\r\n" else 1


@dataclass
class Metadata:
    resolution: float = 0.05
    origin_x: float = 0.0
    origin_y: float = 0.0
    origin_yaw: float = 0.0
    negate: bool = False
    occupied_threshold: float = 0.65
    free_threshold: float = 0.196

    def validate(self):
        values = (self.resolution, self.origin_x, self.origin_y, self.origin_yaw,
                  self.occupied_threshold, self.free_threshold)
        if not all(math.isfinite(value) for value in values):
            raise ValueError("Map metadata must contain finite numbers")
        if self.resolution <= 0:
            raise ValueError("Resolution must be greater than zero")
        if not 0 <= self.free_threshold < self.occupied_threshold <= 1:
            raise ValueError("Free threshold must be lower than occupied threshold")


class OccupancyMap:
    def __init__(self, width=0, height=0, pixels=b"", metadata=None, yaml_path=None):
        self.width = width
        self.height = height
        self.pixels = bytearray(pixels)
        self.metadata = metadata or Metadata()
        self.yaml_path = yaml_path

    @classmethod
    def load(cls, yaml_path):
        path = Path(yaml_path).resolve(strict=True)
        values = {}
        for source in path.read_text(encoding="utf-8").splitlines():
            line = source.strip()
            if line and not line.startswith("#") and ":" in line:
                key, value = line.split(":", 1)
                values[key.strip()] = value.strip().split(" #", 1)[0]
        if "image" not in values:
            raise ValueError("YAML file has no image field")

        origin = values.get("origin", "[0, 0, 0]").strip("[]").split(",")
        if len(origin) != 3:
            raise ValueError("Invalid origin")
        metadata = Metadata(
            float(values.get("resolution", 0.05)),
            float(origin[0]), float(origin[1]), float(origin[2]),
            values.get("negate", "0").lower() in ("1", "true", "yes"),
            float(values.get("occupied_thresh", 0.65)),
            float(values.get("free_thresh", 0.196)),
        )
        metadata.validate()
        image_path = Path(values["image"].strip("\"'"))
        image_path = resolve_within(path.parent, image_path)
        width, height, pixels = cls.read_pgm(image_path)
        return cls(width, height, pixels, metadata, path.resolve())

    @staticmethod
    def read_pgm(path):
        return _PgmReader(Path(path).read_bytes()).read()

    def pgm_bytes(self):
        return f"P5\n{self.width} {self.height}\n255\n".encode() + bytes(self.pixels)

    def save(self, yaml_path=None):
        if not yaml_path and not self.yaml_path:
            raise ValueError("No map destination was selected")
        if self.width <= 0 or self.height <= 0 or len(self.pixels) != self.width * self.height:
            raise ValueError("Map pixel data is invalid")
        self.metadata.validate()
        path = Path(yaml_path or self.yaml_path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        image_path = path.with_suffix(".pgm")
        meta = self.metadata
        yaml_data = (
            f"image: {image_path.name}\nresolution: {meta.resolution}\n"
            f"origin: [{meta.origin_x}, {meta.origin_y}, {meta.origin_yaw}]\n"
            f"negate: {int(meta.negate)}\noccupied_thresh: {meta.occupied_threshold}\n"
            f"free_thresh: {meta.free_threshold}\n"
        )
        image_temp = yaml_temp = None
        try:
            with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
                image_temp = Path(stream.name)
                stream.write(self.pgm_bytes())
            with tempfile.NamedTemporaryFile("w", dir=path.parent, encoding="utf-8",
                                             delete=False) as stream:
                yaml_temp = Path(stream.name)
                stream.write(yaml_data)
            os.replace(image_temp, image_path)
            os.replace(yaml_temp, path)
        finally:
            for temporary in (image_temp, yaml_temp):
                if temporary and temporary.exists():
                    temporary.unlink()
        self.yaml_path = path
