"""Regression tests for the inode diagnostic tool's image path handling."""
import pathlib
import struct
import subprocess
import sys
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).with_name('_dump.py')


class DumpPathTest(unittest.TestCase):
    def test_default_image_is_relative_to_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            scripts = root / 'scripts'
            scripts.mkdir()
            (scripts / '_dump.py').write_bytes(SCRIPT.read_bytes())
            out = root / 'out'
            out.mkdir()
            image = bytearray(8192)
            struct.pack_into('<Q', image, 24, 1)
            (out / 'novus.img').write_bytes(image)
            elsewhere = root / 'elsewhere'
            elsewhere.mkdir()
            result = subprocess.run([sys.executable, str(scripts / '_dump.py')], cwd=elsewhere, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('itbl 1', result.stdout)

    def test_explicit_relative_path_uses_caller_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            image = bytearray(8192)
            struct.pack_into('<Q', image, 24, 1)
            (root / 'custom.img').write_bytes(image)
            result = subprocess.run([sys.executable, str(SCRIPT), 'custom.img'], cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('itbl 1', result.stdout)


if __name__ == '__main__':
    unittest.main()
