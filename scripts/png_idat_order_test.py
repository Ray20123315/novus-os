import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from qemu_smoke import read_png, write_png


class PngIdatOrderTests(unittest.TestCase):
    def test_idat_chunks_must_be_consecutive(self):
        with tempfile.TemporaryDirectory() as work:
            path = Path(work) / "frame.png"
            rgb = bytes((1, 2, 3))
            write_png(path, 1, 1, rgb)
            valid = path.read_bytes()
            self.assertEqual(read_png(path), (1, 1, rgb))

            def chunk(kind, payload):
                return (struct.pack("!I", len(payload)) + kind + payload +
                        struct.pack("!I", zlib.crc32(kind + payload)))

            ihdr_end = 8 + 12 + 13
            idat_size = struct.unpack_from("!I", valid, ihdr_end)[0]
            payload = valid[ihdr_end + 8:ihdr_end + 8 + idat_size]
            split = max(1, len(payload) // 2)
            malformed = (valid[:ihdr_end] +
                         chunk(b"IDAT", payload[:split]) +
                         chunk(b"tEXt", b"note\\0test") +
                         chunk(b"IDAT", payload[split:]) +
                         chunk(b"IEND", b""))
            path.write_bytes(malformed)
            with self.assertRaisesRegex(ValueError, "nonconsecutive PNG IDAT"):
                read_png(path)


if __name__ == "__main__":
    unittest.main()
