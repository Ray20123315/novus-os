import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from qemu_smoke import read_png, write_png


class PngIhdrFirstTests(unittest.TestCase):
    def test_ihdr_must_be_first_chunk(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "frame.png"
            rgb = b"\x01\x02\x03"
            write_png(image, 1, 1, rgb)
            original = image.read_bytes()
            self.assertEqual(read_png(image), (1, 1, rgb))

            kind, payload = b"tEXt", b"comment\x00before header"
            extra = (struct.pack("!I", len(payload)) + kind + payload +
                     struct.pack("!I", zlib.crc32(kind + payload)))
            image.write_bytes(original[:8] + extra + original[8:])
            with self.assertRaisesRegex(ValueError, "IHDR must be the first PNG chunk"):
                read_png(image)


if __name__ == "__main__":
    unittest.main()
