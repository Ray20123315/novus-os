import pathlib
import subprocess
import sys
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).with_name('grep_log.py')


class GrepLogPathTests(unittest.TestCase):
    def test_default_log_is_relative_to_checkout(self):
        with tempfile.TemporaryDirectory() as checkout, tempfile.TemporaryDirectory() as caller:
            root = pathlib.Path(checkout)
            (root / 'scripts').mkdir()
            (root / 'out').mkdir()
            (root / 'out' / 'smoke.log').write_text('ok\nERROR checkout\n')
            target = root / 'scripts' / 'grep_log.py'
            target.write_bytes(SCRIPT.read_bytes())
            result = subprocess.run([sys.executable, str(target)], cwd=caller,
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('ERROR checkout', result.stdout)

    def test_explicit_relative_path_remains_caller_relative(self):
        with tempfile.TemporaryDirectory() as caller:
            pathlib.Path(caller, 'custom.log').write_text('error caller\n')
            result = subprocess.run([sys.executable, str(SCRIPT), 'custom.log'],
                                    cwd=caller, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('error caller', result.stdout)


if __name__ == '__main__':
    unittest.main()
