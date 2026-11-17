#!/usr/bin/env python3
"""Regression tests for FAT 8.3 lookup with non-ASCII path components."""
import unittest

from novusimg import FatFS


class FatLookupUnicodeTests(unittest.TestCase):
    def setUp(self):
        self.fs = FatFS.__new__(FatFS)
        self.fs.entries = lambda cluster: (
            [(b'README  TXT', 2, 8, False),
             (b'SUBDIR     ', 3, 0, True)]
            if cluster == 0 else
            [(b'FILE    BIN', 4, 4, False)]
        )

    def test_ascii_file(self):
        self.assertEqual(self.fs.lookup('README.TXT'), (2, 8, False))

    def test_ascii_nested_file(self):
        self.assertEqual(self.fs.lookup('SUBDIR/FILE.BIN'), (4, 4, False))

    def test_non_ascii_root_component(self):
        self.assertIsNone(self.fs.lookup('中文.TXT'))

    def test_non_ascii_nested_component(self):
        self.assertIsNone(self.fs.lookup('SUBDIR/測試.BIN'))

    def test_missing_ascii_file(self):
        self.assertIsNone(self.fs.lookup('MISSING.TXT'))

    def test_file_as_intermediate_directory(self):
        self.assertIsNone(self.fs.lookup('README.TXT/FILE.BIN'))


if __name__ == '__main__':
    unittest.main()
