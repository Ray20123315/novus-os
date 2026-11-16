"""Regression tests for truncated NovusFS file data."""
import unittest
from unittest.mock import patch

from novusimg import NovusFS


class NovusFileTruncationTests(unittest.TestCase):
    def read(self, blocks, size):
        fs = object.__new__(NovusFS)
        with (patch.object(NovusFS, 'inode', return_value={'size': size}),
              patch.object(NovusFS, '_ids', return_value=iter(range(len(blocks)))),
              patch.object(NovusFS, 'block', side_effect=lambda index: blocks[index])):
            return fs._bytes(1)[0]

    def test_complete_file(self):
        self.assertEqual(self.read([b'abcd', b'efgh'], 6), b'abcdef')

    def test_empty_file(self):
        self.assertEqual(self.read([], 0), b'')

    def test_missing_data_blocks(self):
        with self.assertRaisesRegex(ValueError, 'truncated NovusFS file data'):
            self.read([], 1)

    def test_partial_file_data(self):
        with self.assertRaisesRegex(ValueError, 'truncated NovusFS file data'):
            self.read([b'abc'], 4)


if __name__ == '__main__':
    unittest.main()
