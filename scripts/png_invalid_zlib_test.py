import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from qemu_smoke import read_png, write_png


class PngInvalidZlibTests(unittest.TestCase):
    def test_invalid_zlib_stream_with_valid_chunk_crc(self):
        with tempfile.TemporaryDirectory() as work:
            image = Path(work) / "frame.png"
            write_png(image, 1, 1, b"\x01\x02\x03")
            self.assertEqual(read_png(image), (1, 1, b"\x01\x02\x03"))
            original = image.read_bytes()
            offset = 8 + 25  # Signature plus the fixed 25-byte IHDR chunk.
            self.assertEqual(original[offset + 4:offset + 8], b"IDAT")
            length = struct.unpack_from("!I", original, offset)[0]
            corrupt = b"not-zlib"
            replacement = (struct.pack("!I", len(corrupt)) + b"IDAT" + corrupt +
                           struct.pack("!I", zlib.crc32(b"IDAT" + corrupt)))
            image.write_bytes(original[:offset] + replacement + original[offset + 12 + length:])
            with self.assertRaisesRegex(ValueError, "invalid PNG compressed data"):
                read_png(image)


if __name__ == "__main__":
    unittest.main()
