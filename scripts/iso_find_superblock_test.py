"""Boundary regression tests for the standalone ISO superblock scanner."""
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name('_iso_find.py')
BLOCK = 4096


def superblock():
    data = bytearray(BLOCK)
    struct.pack_into('<I', data, 0, 0x4E4F5653)
    struct.pack_into('<Q', data, 12, 2048)
    struct.pack_into('<Q', data, 24, 12)
    return bytes(data)


class IsoSuperblockBoundaryTests(unittest.TestCase):
    def run_finder(self, iso_data):
        with tempfile.TemporaryDirectory() as directory:
            iso = Path(directory) / 'image.iso'
            ref = Path(directory) / 'reference.img'
            iso.write_bytes(iso_data)
            ref.write_bytes(b'not-in-iso')
            return subprocess.run([sys.executable, str(SCRIPT), str(iso), str(ref)],
                                  capture_output=True, text=True, timeout=3)

    def test_superblock_at_last_complete_block(self):
        result = self.run_finder(bytes(2048) + superblock())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('first off=0x800', result.stdout)

    def test_exactly_one_block_is_scanned(self):
        result = self.run_finder(superblock())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('first off=0x0', result.stdout)

    def test_incomplete_trailing_block_is_not_scanned(self):
        result = self.run_finder(bytes(2048) + superblock()[:4095])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('occurrences=', result.stdout)


if __name__ == '__main__':
    unittest.main()
