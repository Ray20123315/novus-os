"""Regression tests for missing required files with Python assertions disabled."""
import pathlib
import subprocess
import sys
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).with_name('_extract_sys.py')


class ExtractSysMissingTests(unittest.TestCase):
    def run_case(self, system_image, font):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / 'out').mkdir()
            (root / 'input.iso').write_bytes(b'ISO')
            (root / 'novusimg.py').write_text(
                'class IsoFS:\n'
                '    def __init__(self, data): pass\n'
                '    def read_file(self, path, tree): return ' + repr(system_image) + '\n'
                'class NovusFS:\n'
                '    def __init__(self, data): pass\n'
                '    def read_file(self, path): return ' + repr(font) + '\n'
            )
            return subprocess.run(
                [sys.executable, '-O', str(SCRIPT), 'input.iso'],
                cwd=root, capture_output=True, text=True,
                env={**__import__('os').environ, 'PYTHONPATH': str(root)},
            )

    def test_missing_system_image_fails_under_optimized_python(self):
        result = self.run_case(None, b'font')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('SYSTEM.IMG not found', result.stderr)

    def test_missing_font_fails_under_optimized_python(self):
        result = self.run_case(b'system', None)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('/Novus/fonts/font.bin missing', result.stderr)

    def test_present_files_work_under_optimized_python(self):
        result = self.run_case(b'system', b'font')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('font.bin(path): size=4', result.stdout)


if __name__ == '__main__':
    unittest.main()
