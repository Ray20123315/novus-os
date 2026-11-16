"""Regression tests for invalid NovusFS inode numbers."""
import struct
import unittest
from novusimg import NovusFS


class NovusInodeBoundsTests(unittest.TestCase):
    def setUp(self):
        image = bytearray(4 * 4096)
        struct.pack_into('<I', image, 0, 0x4E4F5653)
        struct.pack_into('<I', image, 8, 4096)
        struct.pack_into('<Q', image, 24, 2)
        # Bytes before the inode table resemble a valid inode.
        struct.pack_into('<H', image, 2 * 4096 - 128, 2)
        struct.pack_into('<I', image, 2 * 4096 - 128 + 4, 99)
        struct.pack_into('<H', image, 2 * 4096, 1)
        struct.pack_into('<I', image, 2 * 4096 + 4, 1)
        self.fs = NovusFS(image)

    def test_first_inode(self):
        self.assertEqual(self.fs.inode(1)['ino'], 1)

    def test_zero_inode_does_not_alias_previous_block(self):
        with self.assertRaisesRegex(ValueError, 'inode out of range'):
            self.fs.inode(0)

    def test_negative_inode_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'inode out of range'):
            self.fs.inode(-1)


if __name__ == '__main__':
    unittest.main()
