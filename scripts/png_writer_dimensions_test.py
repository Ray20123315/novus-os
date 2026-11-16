"""Regression tests for PNG dimensions in the QEMU smoke writer."""
import tempfile
import unittest
from pathlib import Path

from qemu_smoke import write_png


class PngWriterDimensionsTests(unittest.TestCase):
    def test_valid_dimensions(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'valid.png'
            write_png(output, 2, 1, b'\x01\x02\x03\x04\x05\x06')
            self.assertTrue(output.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'))

    def test_zero_dimensions_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'invalid.png'
            for width, height in ((0, 1), (1, 0), (0, 0)):
                with self.subTest(width=width, height=height):
                    with self.assertRaisesRegex(ValueError, 'invalid PNG dimensions'):
                        write_png(output, width, height, b'')
                    self.assertFalse(output.exists())

    def test_negative_dimensions_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'invalid.png'
            with self.assertRaisesRegex(ValueError, 'invalid PNG dimensions'):
                write_png(output, -1, 0, b'')
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
