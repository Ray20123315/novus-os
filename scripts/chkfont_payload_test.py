"""Regression tests for an inode whose payload cannot be read."""
import pathlib
import subprocess
import sys
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).with_name('_chkfont.py')


class FontPayloadTests(unittest.TestCase):
    def run_case(self, payload):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / 'novusimg.py').write_text(
                'class NovusFS:\n'
                '    def __init__(self, data): pass\n'
                '    def lookup(self, path): return 2\n'
                '    def inode(self, ino):\n'
                "        return dict(ino=2, mode=1, size=3, blocks=1, direct=[1], iblk=0, diblk=0)\n"
                f'    def read_file(self, path): return {payload}\n', encoding='utf-8')
            (root / '_chkfont.py').write_bytes(SCRIPT.read_bytes())
            (root / 'disk.img').write_bytes(b'dummy')
            return subprocess.run([sys.executable, str(root / '_chkfont.py'), str(root / 'disk.img')],
                                  cwd=root, capture_output=True, text=True)

    def test_unreadable_payload_is_reported(self):
        result = self.run_case('None')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('font payload unavailable', result.stderr)
        self.assertNotIn('TypeError', result.stderr)

    def test_readable_payload_is_printed(self):
        result = self.run_case("b'abc'")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('first data bytes: 616263', result.stdout)


if __name__ == '__main__':
    unittest.main()
