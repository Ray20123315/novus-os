"""Regression tests for the font image comparison helper."""
import pathlib
import subprocess
import sys
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).with_name('_verify_font.py')


class VerifyFontTest(unittest.TestCase):
    def test_reference_font_is_found_outside_repository_cwd(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            (root / 'scripts').mkdir()
            (root / 'graphics').mkdir()
            (root / 'out').mkdir()
            (root / 'graphics' / 'nd_font_data.bin').write_bytes(b'font-data')
            (root / 'out' / 'novus.img').write_bytes(b'font-data')
            (root / 'scripts' / '_verify_font.py').write_bytes(SCRIPT.read_bytes())
            (root / 'scripts' / 'novusimg.py').write_text(
                'class NovusFS:\n'
                '    def __init__(self, data): self.data = data\n'
                '    def lookup(self, path): return 1\n'
                '    def inode(self, ino): return dict(size=9, blocks=1, direct=[], iblk=0, diblk=0)\n'
                '    def read_file(self, path): return self.data\n', encoding='utf-8')
            proc = subprocess.run(
                [sys.executable, str(root / 'scripts' / '_verify_font.py'),
                 str(root / 'out')], cwd='/', capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn('MATCH', proc.stdout)


if __name__ == '__main__':
    unittest.main()
