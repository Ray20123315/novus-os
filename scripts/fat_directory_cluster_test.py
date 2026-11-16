"""Regression tests for malformed FAT subdirectory start clusters."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from novusimg import FatFS, short_name


class FatDirectoryClusterTests(unittest.TestCase):
    @staticmethod
    def reader(root, child=()):
        fs = FatFS.__new__(FatFS)
        fs.entries = lambda cluster: root if cluster == 0 else child
        return fs

    def test_zero_cluster_directory_cannot_alias_root(self):
        fs = self.reader([
            (short_name('EMPTY'), 0, 0, True),
            (short_name('CHILD'), 4, 12, False),
        ])
        with self.assertRaisesRegex(ValueError, 'no starting cluster'):
            fs.lookup('EMPTY/CHILD')

    def test_valid_subdirectory_still_resolves(self):
        fs = self.reader(
            [(short_name('DIR'), 2, 0, True)],
            [(short_name('CHILD'), 4, 12, False)],
        )
        self.assertEqual(fs.lookup('DIR/CHILD'), (4, 12, False))

    def test_root_file_still_resolves(self):
        fs = self.reader([(short_name('CHILD'), 4, 12, False)])
        self.assertEqual(fs.lookup('CHILD'), (4, 12, False))


if __name__ == '__main__':
    unittest.main()
