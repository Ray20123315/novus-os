import pathlib
import subprocess
import sys
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).with_name("grep_log.py")


class GrepLogTest(unittest.TestCase):
    def run_scan(self, content):
        with tempfile.TemporaryDirectory() as tmp:
            log = pathlib.Path(tmp) / "smoke.log"
            log.write_text(content, encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(SCRIPT), str(log)],
                capture_output=True, text=True, check=True,
            ).stdout

    def test_color_codes_inside_keyword_do_not_hide_error(self):
        line = "boot: e\x1b[31mrr\x1b[0mor detected"
        self.assertEqual(self.run_scan(line + "\n"), "0 " + repr(line) + "\n")

    def test_unmatched_line_stays_filtered(self):
        self.assertEqual(self.run_scan("boot complete\n"), "")

    def test_plain_keyword_still_matches(self):
        self.assertEqual(self.run_scan("boot error\n"), "0 'boot error'\n")


if __name__ == "__main__":
    unittest.main()
