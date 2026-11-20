import importlib.util
import struct
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name('extract_fat16.py')
spec = importlib.util.spec_from_file_location('extract_fat16', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def make_image(payload, declared_size):
    # FAT16-like single-file image: boot, FAT, root directory, data cluster.
    image = bytearray(4 * 512)
    struct.pack_into('<H', image, 11, 512)  # bytes per sector
    image[13] = 1  # sectors per cluster
    struct.pack_into('<H', image, 14, 1)  # reserved sectors
    image[16] = 1  # number of FATs
    struct.pack_into('<H', image, 17, 16)  # root directory entries
    struct.pack_into('<H', image, 22, 1)  # FAT sectors
    struct.pack_into('<H', image, 512 + 2 * 2, 0xFFFF)  # cluster 2 is last
    image[1024:1035] = b'SYSTEM  IMG'
    struct.pack_into('<H', image, 1024 + 26, 2)
    struct.pack_into('<I', image, 1024 + 28, declared_size)
    image[1536:1536 + len(payload)] = payload
    return bytes(image)


class ExtractFat16Tests(unittest.TestCase):
    def run_extract(self, image):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'esp.img'
            path.write_bytes(image)
            return module.extract(str(path), 'SYSTEM.IMG')

    def test_valid_file(self):
        self.assertEqual(self.run_extract(make_image(b'hello', 5)), b'hello')

    def test_truncated_image_rejected(self):
        image = make_image(b'hello', 200)[:1536 + 5]
        with self.assertRaisesRegex(ValueError, 'truncated'):
            self.run_extract(image)

    def test_declared_size_exceeds_cluster_chain_rejected(self):
        with self.assertRaisesRegex(ValueError, 'truncated'):
            self.run_extract(make_image(b'hello', 600))


if __name__ == '__main__':
    unittest.main()
