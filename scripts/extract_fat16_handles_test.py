import importlib.util
import os
import struct
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('extract_fat16', os.path.join(os.path.dirname(__file__), 'extract_fat16.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class HandleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, 'esp.img')
        data = bytearray(2048)
        struct.pack_into('<H', data, 11, 512)
        data[13] = 1
        struct.pack_into('<H', data, 14, 1)
        data[16] = 1
        struct.pack_into('<H', data, 17, 16)
        struct.pack_into('<H', data, 22, 1)
        data[1024:1035] = b'SYSTEM  IMG'
        struct.pack_into('<H', data, 1024 + 26, 2)
        struct.pack_into('<I', data, 1024 + 28, 4)
        data[1536:1540] = b'TEST'
        struct.pack_into('<H', data, 512 + 4, 0xFFFF)
        with open(self.path, 'wb') as f:
            f.write(data)

    def assert_closed(self, name, expected=None):
        import builtins
        original_open = builtins.open
        handles = []
        def tracked(*args, **kwargs):
            f = original_open(*args, **kwargs)
            handles.append(f)
            return f
        with patch('builtins.open', side_effect=tracked):
            result = module.extract(self.path, name)
        self.assertEqual(result, expected)
        self.assertTrue(handles and all(f.closed for f in handles), 'extract leaked an open image file')

    def test_found_file_closes_image(self):
        self.assert_closed('SYSTEM.IMG', b'TEST')

    def test_missing_file_closes_image(self):
        self.assert_closed('MISSING.TXT', None)

    def test_invalid_bpb_closes_image_on_exception(self):
        with open(self.path, 'wb') as f:
            f.write(b'bad')
        import builtins
        original_open = builtins.open
        handles = []
        def tracked(*args, **kwargs):
            f = original_open(*args, **kwargs)
            handles.append(f)
            return f
        with patch('builtins.open', side_effect=tracked):
            with self.assertRaises(struct.error):
                module.extract(self.path, 'SYSTEM.IMG')
        self.assertTrue(handles and all(f.closed for f in handles))

if __name__ == '__main__':
    unittest.main()
