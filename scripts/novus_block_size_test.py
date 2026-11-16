"""Regression tests for the frozen NovusFS on-disk block size."""

import struct
import unittest

from novusimg import BLOCK, NOVS_MAGIC, NovusFS


class NovusBlockSizeTests(unittest.TestCase):
    @staticmethod
    def image(block_size):
        data = bytearray(32)
        struct.pack_into('<I', data, 0, NOVS_MAGIC)
        struct.pack_into('<I', data, 8, block_size)
        struct.pack_into('<Q', data, 24, 5)
        return bytes(data)

    def test_valid_block_size(self):
        self.assertEqual(NovusFS(self.image(BLOCK)).bs, BLOCK)

    def test_zero_block_size_rejected(self):
        with self.assertRaisesRegex(ValueError, 'block size'):
            NovusFS(self.image(0))

    def test_other_block_size_rejected(self):
        with self.assertRaisesRegex(ValueError, 'block size'):
            NovusFS(self.image(512))


if __name__ == '__main__':
    unittest.main()
