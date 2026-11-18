"""Regression tests for the standalone ISO image finder."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name('_iso_find.py')


class IsoFindTests(unittest.TestCase):
    def run_finder(self, iso_data, ref_data):
        with tempfile.TemporaryDirectory() as directory:
            iso = Path(directory) / 'image.iso'
            ref = Path(directory) / 'reference.img'
            iso.write_bytes(iso_data)
            ref.write_bytes(ref_data)
            return subprocess.run([sys.executable, str(SCRIPT), str(iso), str(ref)],
                                  capture_output=True, text=True, timeout=2)

    def test_empty_reference_is_rejected(self):
        result = self.run_finder(b'ABCDEF', b'')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('empty reference image', result.stderr)

    def test_embedded_reference_is_found(self):
        result = self.run_finder(b'0123ABCD789', b'ABCD')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('matches: 1', result.stdout)

    def test_missing_reference_is_reported(self):
        result = self.run_finder(b'0123456789', b'ABCD')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('matches: 0', result.stdout)


if __name__ == '__main__':
    unittest.main()
