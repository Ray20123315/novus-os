"""Regression tests for NovusFS fixed-size directory slots.

Run with: python3 -m unittest discover -s scripts -p novus_dirent_bounds_test.py
"""
import struct
import unittest

from novusimg import NovusFS


def reader(buf):
    fs = object.__new__(NovusFS)
    fs._bytes = lambda ino: (buf, {'mode': 2})
    return fs


def slot(ino, name, rec=64, nlen=None):
    data = bytearray(64)
    if nlen is None:
        nlen = len(name)
    struct.pack_into('<IHH', data, 0, ino, rec, nlen)
    data[8:8 + min(len(name), 56)] = name[:56]
    return bytes(data)


class DirentBoundsTest(unittest.TestCase):
    def test_valid_adjacent_slots(self):
        self.assertEqual(
            reader(slot(3, b'alpha') + slot(4, b'beta')).dirents(1),
            [(3, 'alpha'), (4, 'beta')])

    def test_reject_cross_slot_name_and_keep_next(self):
        bad = slot(3, b'A' * 56, nlen=60)
        self.assertEqual(reader(bad + slot(4, b'beta')).dirents(1),
                         [(4, 'beta')])

    def test_reject_invalid_record_length_and_keep_next(self):
        self.assertEqual(
            reader(slot(3, b'alpha', rec=8) + slot(4, b'beta')).dirents(1),
            [(4, 'beta')])

    def test_reject_truncated_slot(self):
        self.assertEqual(reader(slot(3, b'alpha')[:15]).dirents(1), [])

    def test_skip_empty_slot(self):
        self.assertEqual(reader(slot(0, b'') + slot(4, b'beta')).dirents(1),
                         [(4, 'beta')])


if __name__ == '__main__':
    unittest.main()
