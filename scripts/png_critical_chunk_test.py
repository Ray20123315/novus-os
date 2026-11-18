import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from qemu_smoke import read_png, write_png


class PngCriticalChunkTests(unittest.TestCase):
    def test_unknown_critical_chunk_is_rejected(self):
        with tempfile.TemporaryDirectory() as work:
            path = Path(work) / "frame.png"
            rgb = bytes((1, 2, 3))
            write_png(path, 1, 1, rgb)
            valid = path.read_bytes()
            self.assertEqual(read_png(path), (1, 1, rgb))

            ihdr_end = 8 + 12 + 13
            kind = b"ABCD"
            chunk = struct.pack("!I", 0) + kind + struct.pack("!I", zlib.crc32(kind))
            path.write_bytes(valid[:ihdr_end] + chunk + valid[ihdr_end:])
            with self.assertRaisesRegex(ValueError, "unknown critical PNG chunk"):
                read_png(path)

            kind = b"abCD"  # Unknown ancillary chunks may be skipped.
            chunk = struct.pack("!I", 0) + kind + struct.pack("!I", zlib.crc32(kind))
            path.write_bytes(valid[:ihdr_end] + chunk + valid[ihdr_end:])
            self.assertEqual(read_png(path), (1, 1, rgb))


if __name__ == "__main__":
    unittest.main()
