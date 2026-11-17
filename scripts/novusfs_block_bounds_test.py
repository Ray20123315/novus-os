#!/usr/bin/env python3
"""Regression tests for NovusFS block boundaries."""
import unittest

from novusimg import NovusFS


class NovusFSBlockBoundsTest(unittest.TestCase):
    def reader(self, data):
        fs = object.__new__(NovusFS)
        fs.data = data
        fs.bs = 4096
        return fs

    def test_complete_block(self):
        fs = self.reader(b"A" * 4096 + b"B" * 4096)
        self.assertEqual(fs.block(1), b"B" * 4096)

    def test_partial_block(self):
        fs = self.reader(b"A" * 4096 + b"B" * 7)
        with self.assertRaisesRegex(ValueError, "outside image"):
            fs.block(1)

    def test_missing_block(self):
        fs = self.reader(b"A" * 4096)
        with self.assertRaises(ValueError):
            fs.block(1)

    def test_negative_block_number(self):
        fs = self.reader(b"A" * 8192)
        with self.assertRaises(ValueError):
            fs.block(-1)


if __name__ == "__main__":
    unittest.main()
