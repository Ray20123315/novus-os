"""Regression tests for serial log scanning."""
import pathlib
import subprocess
import sys
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).with_name("grep_log.py")


class GrepLogTests(unittest.TestCase):
    def test_invalid_utf8_does_not_hide_later_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "smoke.log"
            path.write_bytes(b"boot\ninvalid: \xff\npanic: test failure\n")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path)],
                capture_output=True, text=True, check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("panic: test failure", result.stdout)
        self.assertIn("2 ", result.stdout)

    def test_normal_log_still_filters_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "smoke.log"
            path.write_text("boot\nerror: disk\nready\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path)],
                capture_output=True, text=True, check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1 'error: disk'", result.stdout)
        self.assertNotIn("ready", result.stdout)


if __name__ == "__main__":
    unittest.main()
