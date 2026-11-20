"""Regression coverage for a NovusFS inode whose font payload cannot be read."""
import pathlib
import subprocess
import sys
import tempfile
import unittest


SCRIPT = pathlib.Path(__file__).with_name('_verify_font.py')


class MissingFontPayloadTest(unittest.TestCase):
    def test_unreadable_font_payload_reports_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / 'out').mkdir()
            (root / 'out' / 'novus.img').write_bytes(b'test-image')
            (root / 'graphics').mkdir()
            (root / 'graphics' / 'nd_font_data.bin').write_bytes(b'font')
            (root / 'scripts').mkdir()
            (root / 'scripts' / '_verify_font.py').write_bytes(SCRIPT.read_bytes())
            (root / 'scripts' / 'novusimg.py').write_text('''
class NovusFS:
    def __init__(self, data): pass
    def lookup(self, path): return 1
    def inode(self, ino):
        return dict(size=4, blocks=1, direct=[0], iblk=0, diblk=0)
    def read_file(self, path): return None
''')
            proc = subprocess.run([sys.executable, str(root / 'scripts' / '_verify_font.py'),
                                   str(root / 'out')], cwd=root, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn('MISSING /Novus/fonts/font.bin', proc.stdout)
            self.assertNotIn('Traceback', proc.stderr)


if __name__ == '__main__':
    unittest.main()
