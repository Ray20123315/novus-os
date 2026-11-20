"""Regression tests for the SYSTEM.IMG extraction helper."""
import pathlib
import subprocess
import sys
import tempfile
import unittest


SCRIPT = pathlib.Path(__file__).with_name('_extract_sys.py')


class ExtractSystemTests(unittest.TestCase):
    def test_output_is_relative_to_checkout_not_caller(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp) / 'checkout with spaces'
            scripts = root / 'scripts'
            scripts.mkdir(parents=True)
            (root / 'out').mkdir()
            caller = pathlib.Path(temp) / 'other directory'
            caller.mkdir()
            (scripts / '_extract_sys.py').write_bytes(SCRIPT.read_bytes())
            (scripts / 'novusimg.py').write_text(
                'class IsoFS:\n'
                '    def __init__(self, data): pass\n'
                '    def read_file(self, path, tree):\n'
                '        assert (path, tree) == ("SYSTEM.IMG", "primary")\n'
                '        return b"system-image"\n'
                'class NovusFS:\n'
                '    def __init__(self, data): assert data == b"system-image"\n'
                '    def read_file(self, path):\n'
                '        assert path == "Novus/fonts/font.bin"\n'
                '        return b"font"\n', encoding='utf-8')
            iso = caller / 'source.iso'
            iso.write_bytes(b'iso')
            result = subprocess.run(
                [sys.executable, str(scripts / '_extract_sys.py'), str(iso)],
                cwd=caller, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((root / 'out' / 'sys_extracted.img').read_bytes(),
                             b'system-image')
            self.assertFalse((caller / 'out' / 'sys_extracted.img').exists())


if __name__ == '__main__':
    unittest.main()
