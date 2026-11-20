"""Regression tests for the block-130 diagnostic helper."""
import pathlib
import struct
import subprocess
import sys
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).with_name('_blk130.py')


class Block130Test(unittest.TestCase):
    def test_default_image_is_checkout_relative(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            script = root / 'scripts' / '_blk130.py'
            script.parent.mkdir()
            script.write_bytes(SCRIPT.read_bytes())
            image = root / 'out' / 'novus.img'
            image.parent.mkdir()
            block = bytearray(4096)
            struct.pack_into('<QQ', block, 0, 0x48DBBF0F48DA29F2, 0xBF0F48C8394CD829)
            image.write_bytes(bytes(130 * 4096) + block)
            result = subprocess.run([sys.executable, str(script)], cwd='/', text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('MATCH block130[0:16]? True', result.stdout)

    def test_explicit_image_and_truncation(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = pathlib.Path(tmp) / 'short.img'
            image.write_bytes(bytes(130 * 4096))
            result = subprocess.run([sys.executable, str(SCRIPT), str(image)], cwd='/', text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('truncated', result.stderr)


if __name__ == '__main__':
    unittest.main()
