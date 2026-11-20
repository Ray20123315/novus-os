"""Regression coverage for missing font in optimized Python."""
import pathlib
import subprocess
import sys
import tempfile
import unittest


SCRIPT = pathlib.Path(__file__).with_name('_chkfont.py')


class FontMissingTest(unittest.TestCase):
    def test_missing_font_under_optimized_python(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / 'novusimg.py').write_text(
                'class NovusFS:\n'
                '    def __init__(self, data): pass\n'
                '    def lookup(self, path): return 0\n'
                '    def inode(self, ino): raise RuntimeError("inode called")\n',
                encoding='utf-8',
            )
            (root / '_chkfont.py').write_bytes(SCRIPT.read_bytes())
            (root / 'test.img').write_bytes(b'test')
            proc = subprocess.run(
                [sys.executable, '-O', str(root / '_chkfont.py'), str(root / 'test.img')],
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn('/Novus/fonts/font.bin not found', proc.stderr)
            self.assertNotIn('inode called', proc.stderr)


    def test_present_font_under_optimized_python(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / 'novusimg.py').write_text(
                'class NovusFS:\n'
                '    def __init__(self, data): pass\n'
                '    def lookup(self, path): return 2\n'
                '    def inode(self, ino):\n'
                '        return dict(ino=ino, mode=1, size=4, blocks=1, direct=[3], iblk=0, diblk=0)\n'
                '    def read_file(self, path): return b"font"\n',
                encoding='utf-8',
            )
            (root / '_chkfont.py').write_bytes(SCRIPT.read_bytes())
            (root / 'test.img').write_bytes(b'test')
            proc = subprocess.run(
                [sys.executable, '-O', str(root / '_chkfont.py'), str(root / 'test.img')],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn('font.bin inode=2', proc.stdout)
            self.assertIn('666f6e74', proc.stdout)


if __name__ == '__main__':
    unittest.main()
