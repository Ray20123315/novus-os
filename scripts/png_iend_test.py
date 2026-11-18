"""Regression tests for PNG IEND validation in the smoke baseline reader."""

import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from qemu_smoke import read_png, write_png


def chunk(kind: bytes, payload: bytes) -> bytes:
    return (struct.pack("!I", len(payload)) + kind + payload +
            struct.pack("!I", zlib.crc32(kind + payload)))


class PngIendTests(unittest.TestCase):
    def test_iend_rejects_trailing_data_and_nonempty_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "baseline.png"
            write_png(path, 1, 1, b"\x01\x02\x03")
            valid = path.read_bytes()
            self.assertEqual(read_png(path), (1, 1, b"\x01\x02\x03"))

            invalid = (
                valid + b"junk",
                valid + chunk(b"tEXt", b"junk"),
                valid[:-12] + chunk(b"IEND", b"x"),
            )
            for image in invalid:
                with self.subTest(image=image[-20:]):
                    path.write_bytes(image)
                    with self.assertRaises(ValueError):
                        read_png(path)


if __name__ == "__main__":
    unittest.main()
