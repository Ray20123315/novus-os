"""Regression tests for the checkout-relative default font image path."""
import pathlib
import subprocess
import sys
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).with_name('_chkfont.py')
STUB = '''class NovusFS:
    def __init__(self, data):
        if data != b"FONT-IMAGE":
            raise ValueError("wrong image")
    def lookup(self, path):
        return 7
    def inode(self, ino):
        return dict(ino=ino, mode=1, size=4, blocks=1, direct=[1], iblk=0, diblk=0)
    def read_file(self, path):
        return b"FONT"
'''

class FontPathTest(unittest.TestCase):
    def test_default_image_relative_to_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            scripts = root / 'checkout' / 'scripts'
            scripts.mkdir(parents=True)
            (scripts / '_chkfont.py').write_bytes(SCRIPT.read_bytes())
            (scripts / 'novusimg.py').write_text(STUB)
            out = root / 'checkout' / 'out'
            out.mkdir()
            (out / 'novus.img').write_bytes(b'FONT-IMAGE')
            result = subprocess.run([sys.executable, str(scripts / '_chkfont.py')],
                                    cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('font.bin inode=7', result.stdout)

    def test_explicit_image_is_caller_relative(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            scripts = root / 'checkout' / 'scripts'
            scripts.mkdir(parents=True)
            (scripts / '_chkfont.py').write_bytes(SCRIPT.read_bytes())
            (scripts / 'novusimg.py').write_text(STUB)
            (root / 'custom.img').write_bytes(b'FONT-IMAGE')
            result = subprocess.run([sys.executable, str(scripts / '_chkfont.py'), 'custom.img'],
                                    cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('first data bytes: 464f4e54', result.stdout)

if __name__ == '__main__':
    unittest.main()
