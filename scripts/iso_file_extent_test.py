#!/usr/bin/env python3
"""Regression tests for ISO file extents that exceed the image."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from novusimg import IsoFS


class IsoFileExtentTests(unittest.TestCase):
    def reader(self, data, lba, size, is_dir=False):
        iso = IsoFS.__new__(IsoFS)
        iso.data = data
        iso.lookup = lambda path, name_set='joliet': (
            (lba, size, is_dir) if path == 'FILE' else None
        )
        return iso

    def test_valid_extent(self):
        iso = self.reader(b'\0' * 2048 + b'abc', 1, 3)
        self.assertEqual(iso.read_file('FILE'), b'abc')

    def test_truncated_extent(self):
        iso = self.reader(b'\0' * 2048 + b'ab', 1, 3)
        with self.assertRaisesRegex(ValueError, 'ISO file extent outside image'):
            iso.read_file('FILE')

    def test_extent_starts_past_end(self):
        iso = self.reader(b'\0' * 2048, 2, 1)
        with self.assertRaisesRegex(ValueError, 'ISO file extent outside image'):
            iso.read_file('FILE')

    def test_empty_file(self):
        self.assertEqual(self.reader(b'', 0, 0).read_file('FILE'), b'')

    def test_missing_or_directory(self):
        iso = self.reader(b'', 0, 0, is_dir=True)
        self.assertIsNone(iso.read_file('FILE'))
        self.assertIsNone(iso.read_file('MISSING'))


if __name__ == '__main__':
    unittest.main()
