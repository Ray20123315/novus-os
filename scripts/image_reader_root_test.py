"""Regression tests for root-directory paths in image readers."""
import unittest
from unittest.mock import Mock

from novusimg import FatFS, IsoFS


class RootDirectoryTests(unittest.TestCase):
    def test_slash_only_paths_are_directories(self):
        for reader in (FatFS, IsoFS):
            fs = reader.__new__(reader)
            fs.lookup = Mock(side_effect=AssertionError("root must not be looked up"))
            for path in ("", "/", "///"):
                with self.subTest(reader=reader.__name__, path=path):
                    self.assertTrue(fs.is_dir(path))
            fs.lookup.assert_not_called()

    def test_non_root_paths_still_use_lookup(self):
        for reader in (FatFS, IsoFS):
            fs = reader.__new__(reader)
            fs.lookup = Mock(return_value=(2, 0, True))
            self.assertTrue(fs.is_dir("/SUBDIR"))
            fs.lookup.assert_called_once()

    def test_missing_non_root_paths_are_not_directories(self):
        for reader in (FatFS, IsoFS):
            fs = reader.__new__(reader)
            fs.lookup = Mock(return_value=None)
            self.assertFalse(fs.is_dir("/MISSING"))


if __name__ == "__main__":
    unittest.main()
