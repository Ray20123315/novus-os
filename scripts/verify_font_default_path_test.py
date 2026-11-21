"""Verify default checkout path and caller-relative explicit paths."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent


class VerifyFontDefaultPathTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.checkout = self.root / 'checkout'
        scripts = self.checkout / 'scripts'
        scripts.mkdir(parents=True)
        shutil.copyfile(HERE / '_verify_font.py', scripts / '_verify_font.py')
        (scripts / 'novusimg.py').write_text('''\
class NovusFS:
    def __init__(self, data):
        self.data = data
    def lookup(self, path):
        return 1
    def inode(self, ino):
        return {'size': len(self.data), 'blocks': 1, 'direct': [1], 'iblk': 0, 'diblk': 0}
    def read_file(self, path):
        return self.data
''', encoding='utf-8')
        (self.checkout / 'out').mkdir()
        (self.checkout / 'out' / 'novus.img').write_bytes(b'checkout-font')
        self.caller = self.root / 'caller'
        (self.caller / 'graphics').mkdir(parents=True)
        (self.caller / 'graphics' / 'nd_font_data.bin').write_bytes(b'checkout-font')
        self.script = scripts / '_verify_font.py'

    def run_tool(self, *args):
        return subprocess.run([sys.executable, str(self.script), *args],
                              cwd=self.caller, text=True, capture_output=True,
                              check=False)

    def test_default_image_is_relative_to_checkout(self):
        result = self.run_tool()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('MATCH', result.stdout)

    def test_explicit_relative_directory_uses_caller(self):
        (self.caller / 'custom').mkdir()
        (self.caller / 'custom' / 'novus.img').write_bytes(b'checkout-font')
        result = self.run_tool('custom')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('MATCH', result.stdout)


if __name__ == '__main__':
    unittest.main()
