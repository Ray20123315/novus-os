"""Regression tests for ISO 9660 directory record identifier boundaries."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from novusimg import IsoFS


def record(identifier, declared_length=None):
    raw = bytearray(33 + len(identifier))
    raw[0] = len(raw)
    raw[32] = len(identifier) if declared_length is None else declared_length
    raw[33:] = identifier
    return bytes(raw)


def names(data, name_set='primary', pad=True):
    if pad:
        data = data.ljust(2048, b'\0')
    return [name for name, *_ in IsoFS(data).entries(0, 2048, name_set)]


class IsoDirectoryRecordTests(unittest.TestCase):
    def test_primary_identifier(self):
        self.assertEqual(names(record(b'FILE.TXT;1')), ['FILE.TXT'])

    def test_joliet_identifier(self):
        self.assertEqual(names(record('HELLO'.encode('utf-16-be')), 'joliet'),
                         ['HELLO'])

    def test_overlong_identifier_does_not_consume_next_record(self):
        malformed = record(b'A', declared_length=10)
        following = record(b'NEXT.TXT;1')
        self.assertEqual(names(malformed + following), ['NEXT.TXT'])

    def test_record_extending_beyond_available_data_is_ignored(self):
        truncated = bytearray(record(b'ABC'))
        truncated[0] = 40
        self.assertEqual(names(bytes(truncated), pad=False), [])


if __name__ == '__main__':
    unittest.main()
