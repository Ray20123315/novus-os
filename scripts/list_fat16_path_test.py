"""Regression tests for list_fat16.py image path resolution."""
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPT = pathlib.Path(__file__).with_name('list_fat16.py')


class ListFat16PathTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.scripts = self.root / 'scripts'
        self.scripts.mkdir()
        shutil.copyfile(SCRIPT, self.scripts / 'list_fat16.py')
        (self.scripts / 'novusimg.py').write_text(
            'class FatFS:\n'
            '    bps = 512\n'
            '    spc = 1\n'
            '    res = 1\n'
            '    nf = 2\n'
            '    fat_sz = 8\n'
            '    def __init__(self, data):\n'
            '        assert data == b"valid-image"\n'
            '    def entries(self, cluster):\n'
            '        return []\n', encoding='utf-8')
        (self.root / 'out').mkdir()
        (self.root / 'out' / 'esp.img').write_bytes(b'valid-image')
        self.other = self.root / 'other'
        self.other.mkdir()

    def run_script(self, *args):
        return subprocess.run([sys.executable, str(self.scripts / 'list_fat16.py'), *args],
                              cwd=self.other, text=True, capture_output=True, check=False)

    def test_default_image_is_checkout_relative(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('0 entries', result.stdout)

    def test_explicit_relative_image_remains_cwd_relative(self):
        (self.other / 'chosen.img').write_bytes(b'valid-image')
        result = self.run_script('chosen.img')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('chosen.img: bps=512', result.stdout)


if __name__ == '__main__':
    unittest.main()
