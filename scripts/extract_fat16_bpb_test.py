import importlib.util
import struct
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name('extract_fat16.py')
spec = importlib.util.spec_from_file_location('extract_fat16', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def image():
    data = bytearray(4 * 512)
    struct.pack_into('<H', data, 11, 512)
    data[13] = 1
    struct.pack_into('<H', data, 14, 1)
    data[16] = 1
    struct.pack_into('<H', data, 17, 16)
    struct.pack_into('<H', data, 22, 1)
    struct.pack_into('<H', data, 512 + 4, 0xFFFF)
    data[1024:1035] = b'SYSTEM  IMG'
    struct.pack_into('<H', data, 1024 + 26, 2)
    struct.pack_into('<I', data, 1024 + 28, 5)
    data[1536:1541] = b'hello'
    return data


class BpbValidationTests(unittest.TestCase):
    def extract(self, data):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'esp.img'
            path.write_bytes(data)
            return module.extract(str(path), 'SYSTEM.IMG')

    def test_valid_image(self):
        self.assertEqual(self.extract(image()), b'hello')

    def test_short_boot_sector(self):
        with self.assertRaisesRegex(ValueError, 'boot sector'):
            self.extract(b'\0' * 10)

    def test_zero_bytes_per_sector(self):
        data = image()
        struct.pack_into('<H', data, 11, 0)
        with self.assertRaisesRegex(ValueError, 'bytes per sector'):
            self.extract(data)

    def test_zero_sectors_per_cluster(self):
        data = image()
        data[13] = 0
        with self.assertRaisesRegex(ValueError, 'sectors per cluster'):
            self.extract(data)


if __name__ == '__main__':
    unittest.main()
