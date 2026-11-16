#!/usr/bin/env python3
"""Regression tests for truncated NovusFS superblocks."""
import struct
import unittest

from novusimg import NOVS_MAGIC, NovusFS


class NovusSuperblockBoundsTests(unittest.TestCase):
    def test_truncated_superblocks_raise_value_error(self):
        for length in (0, 1, 3, 4, 8, 12, 24, 31):
            with self.subTest(length=length):
                data = bytearray(length)
                if length >= 4:
                    struct.pack_into('<I', data, 0, NOVS_MAGIC)
                with self.assertRaisesRegex(ValueError, 'truncated NovusFS superblock'):
                    NovusFS(data)

    def test_complete_header(self):
        data = bytearray(32)
        struct.pack_into('<I', data, 0, NOVS_MAGIC)
        struct.pack_into('<I', data, 8, 4096)
        struct.pack_into('<Q', data, 24, 8)
        fs = NovusFS(data)
        self.assertEqual((fs.bs, fs.itbl, fs.root), (4096, 8, 1))

    def test_bad_magic(self):
        with self.assertRaisesRegex(ValueError, 'not a NovusFS image'):
            NovusFS(bytes(32))


if __name__ == '__main__':
    unittest.main()
