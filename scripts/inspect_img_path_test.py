"""Regression tests for the image inspector's default input path."""
import pathlib
import subprocess
import sys
import tempfile
import unittest


SCRIPT = pathlib.Path(__file__).with_name('inspect_img.py')


class InspectImagePathTest(unittest.TestCase):
    def test_default_image_is_relative_to_checkout(self):
        with tempfile.TemporaryDirectory(prefix='novus inspect ') as tmp:
            root = pathlib.Path(tmp) / 'checkout with spaces'
            scripts = root / 'scripts'
            scripts.mkdir(parents=True)
            (root / 'out').mkdir()
            (root / 'out' / 'novus.img').write_bytes(b'test-image')
            (scripts / 'inspect_img.py').write_bytes(SCRIPT.read_bytes())
            (scripts / 'novusimg.py').write_text(
                'class NovusFS:\n'
                '    def __init__(self, data):\n'
                '        assert data == b"test-image"\n'
                '        self.bs, self.itbl, self.root = 4096, 8, 1\n'
                '    def dirents(self, ino):\n'
                '        return []\n'
                'def u32(*args): pass\n'
                'def u64(*args): pass\n', encoding='utf-8')
            caller = pathlib.Path(tmp) / 'elsewhere'
            caller.mkdir()
            result = subprocess.run([sys.executable, str(scripts / 'inspect_img.py')],
                                    cwd=caller, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('0 entries', result.stdout)
            self.assertIn(str(root / 'out' / 'novus.img'), result.stdout)


if __name__ == '__main__':
    unittest.main()
