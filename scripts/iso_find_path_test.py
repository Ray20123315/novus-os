"""Regression tests for ISO diagnostic default image paths."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parent / '_iso_find.py'


class IsoFindPathTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.checkout = self.root / 'checkout'
        scripts = self.checkout / 'scripts'
        scripts.mkdir(parents=True)
        self.script = scripts / '_iso_find.py'
        shutil.copyfile(SCRIPT, self.script)
        out = self.checkout / 'out'
        out.mkdir()
        (out / 'novus.img').write_bytes(b'REF-DATA')
        (out / 'novus-live.iso').write_bytes(b'\x00' * 4096 + b'REF-DATA' + b'\x00' * 4096)
        self.external = self.root / 'elsewhere'
        self.external.mkdir()

    def test_defaults_are_relative_to_checkout(self):
        result = subprocess.run([sys.executable, str(self.script)], cwd=self.external,
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('matches: 1', result.stdout)

    def test_explicit_relative_paths_are_relative_to_caller(self):
        (self.external / 'other.iso').write_bytes(b'ABC123')
        (self.external / 'other.img').write_bytes(b'ABC123')
        result = subprocess.run([sys.executable, str(self.script), 'other.iso', 'other.img'],
                                cwd=self.external, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('matches: 1', result.stdout)


if __name__ == '__main__':
    unittest.main()
