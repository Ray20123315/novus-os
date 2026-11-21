import pathlib
import struct
import subprocess
import sys
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).with_name('_dump.py')


class DumpTruncatedTest(unittest.TestCase):
    def run_dump(self, image):
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / 'out'
            out.mkdir()
            (out / 'novus.img').write_bytes(image)
            return subprocess.run([sys.executable, str(SCRIPT)], cwd=tmp,
                                  capture_output=True, text=True, check=False)

    def test_valid_inode(self):
        image = bytearray(8192)
        struct.pack_into('<Q', image, 24, 1)
        struct.pack_into('<Q', image, 4096 + 128, 12345)
        result = self.run_dump(image)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('0 12345', result.stdout)

    def test_truncated_superblock(self):
        result = self.run_dump(b'NOVS')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('truncated NovusFS superblock', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_truncated_inode(self):
        image = bytearray(4096 + 128 + 16)
        struct.pack_into('<Q', image, 24, 1)
        result = self.run_dump(image)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('truncated inode 2', result.stderr)
        self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
