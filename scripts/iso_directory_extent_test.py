"""Regression tests for ISO directory extents shorter than a sector."""
import struct
import unittest

from novusimg import IsoFS


def record(name):
    entry = bytearray(33 + len(name))
    entry[0] = len(entry)
    entry[32] = len(name)
    entry[33:] = name
    struct.pack_into('<I', entry, 2, 22)
    struct.pack_into('<I', entry, 10, 123)
    return bytes(entry)


class IsoDirectoryExtentTests(unittest.TestCase):
    def test_entry_within_extent(self):
        first = record(b'GOOD;1')
        reader = object.__new__(IsoFS)
        reader.data = first
        self.assertEqual(reader.entries(0, len(first), 'primary'),
                         [('GOOD', 22, 123, False)])

    def test_entry_beyond_declared_extent_is_ignored(self):
        first, second = record(b'GOOD;1'), record(b'BAD;1')
        reader = object.__new__(IsoFS)
        reader.data = first + second
        self.assertEqual([entry[0] for entry in reader.entries(0, len(first), 'primary')],
                         ['GOOD'])

    def test_partial_record_beyond_extent_is_ignored(self):
        first, second = record(b'GOOD;1'), record(b'BAD;1')
        reader = object.__new__(IsoFS)
        reader.data = first + second
        self.assertEqual([entry[0] for entry in reader.entries(0, len(first) + 10, 'primary')],
                         ['GOOD'])


if __name__ == '__main__':
    unittest.main()
