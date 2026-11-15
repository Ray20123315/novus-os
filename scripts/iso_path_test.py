"""Regression tests for ISO 9660 path traversal through regular files.

Run with: python3 -m unittest discover -s scripts -p iso_path_test.py
"""

import unittest
from unittest.mock import patch

from novusimg import IsoFS


class IsoPathTests(unittest.TestCase):
    def setUp(self):
        # Use a tiny synthetic directory tree so the path-walking logic is
        # exercised independently of ISO descriptor and extent generation.
        self.iso = IsoFS.__new__(IsoFS)
        self.iso.trees = {'primary': (20, 2048), 'joliet': (30, 2048)}
        self.iso.data = b''
        self.entries = {
            20: [('FILE.TXT', 40, 2048, False), ('DIR', 50, 2048, True)],
            30: [('FILE.TXT', 40, 2048, False), ('DIR', 50, 2048, True)],
            40: [('FORGED', 60, 5, False)],
            50: [('CHILD.TXT', 70, 5, False)],
        }
        self.seen = []

        def entries(lba, size, name_set='joliet'):
            self.seen.append(lba)
            return self.entries.get(lba, [])

        patcher = patch.object(self.iso, 'entries', side_effect=entries)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_rejects_file_as_intermediate_path_component(self):
        for tree in ('primary', 'joliet'):
            with self.subTest(tree=tree):
                self.seen.clear()
                self.assertIsNone(self.iso.lookup('FILE.TXT/FORGED', tree))
                self.assertNotIn(40, self.seen)

    def test_directory_traversal_still_works(self):
        for tree in ('primary', 'joliet'):
            with self.subTest(tree=tree):
                self.assertEqual(self.iso.lookup('DIR/CHILD.TXT', tree),
                                 (70, 5, False))

    def test_regular_file_and_missing_path(self):
        self.assertEqual(self.iso.lookup('FILE.TXT'), (40, 2048, False))
        self.assertIsNone(self.iso.lookup('MISSING/FORGED'))


if __name__ == '__main__':
    unittest.main()
