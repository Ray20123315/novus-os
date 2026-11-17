"""Regression tests for ISO 9660 primary-only name lookup."""
import struct
import unittest

from novusimg import IsoFS


def make_fs(include_joliet=False):
    fs = IsoFS.__new__(IsoFS)
    fs.trees = {'primary': (20, 2048)}
    if include_joliet:
        fs.trees['joliet'] = (22, 2048)
    data = bytearray(24 * 2048)
    for lba, name in [(20, b'README.TXT;1'),
                      (22, 'README.TXT;1'.encode('utf-16-be'))]:
        offset = lba * 2048
        data[offset] = 33 + len(name)
        struct.pack_into('<I', data, offset + 2, 21)
        struct.pack_into('<I', data, offset + 10, 5)
        data[offset + 32] = len(name)
        data[offset + 33:offset + 33 + len(name)] = name
    fs.data = bytes(data)
    return fs


class IsoPrimaryFallbackTests(unittest.TestCase):
    def test_default_lookup_uses_primary_decoding_without_joliet(self):
        self.assertEqual(make_fs().lookup('/README.TXT'), (21, 5, False))

    def test_explicit_primary_lookup(self):
        self.assertEqual(make_fs().lookup('/README.TXT', 'primary'),
                         (21, 5, False))

    def test_joliet_lookup_still_works(self):
        self.assertEqual(make_fs(True).lookup('/README.TXT'),
                         (21, 5, False))

    def test_missing_name(self):
        self.assertIsNone(make_fs().lookup('/MISSING.TXT'))


if __name__ == '__main__':
    unittest.main()
