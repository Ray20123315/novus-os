"""Regression tests for overlapping embedded image matches."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name('_iso_find.py')


class IsoFindOverlapTests(unittest.TestCase):
    def run_finder(self, image, reference):
        with tempfile.TemporaryDirectory() as directory:
            iso = Path(directory) / 'image.iso'
            ref = Path(directory) / 'reference.img'
            iso.write_bytes(image)
            ref.write_bytes(reference)
            return subprocess.run([sys.executable, str(SCRIPT), str(iso), str(ref)],
                                  capture_output=True, text=True, timeout=3)

    def test_overlapping_matches_are_all_reported(self):
        result = self.run_finder(b'ABABA', b'ABA')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('MATCH at iso offset 0 ', result.stdout)
        self.assertIn('MATCH at iso offset 2 ', result.stdout)
        self.assertIn('matches: 2', result.stdout)

    def test_nonoverlapping_matches_remain_reported(self):
        result = self.run_finder(b'ABC-ABC', b'ABC')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('matches: 2', result.stdout)

    def test_absent_reference(self):
        result = self.run_finder(b'ABABA', b'XYZ')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('matches: 0', result.stdout)


if __name__ == '__main__':
    unittest.main()
