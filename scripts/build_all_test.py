"""Regression test for build-all.sh checkout-relative execution."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


class BuildAllTests(unittest.TestCase):
    def test_invoked_outside_checkout_uses_script_checkout(self):
        script = Path(__file__).with_name("build-all.sh")
        with tempfile.TemporaryDirectory() as work:
            root = Path(work) / "checkout"
            (root / "scripts").mkdir(parents=True)
            (root / "scripts" / "build-all.sh").write_bytes(script.read_bytes())
            tools = Path(work) / "tools"
            tools.mkdir()
            log = Path(work) / "calls.log"
            for command in ("make", "python3"):
                mock = tools / command
                mock.write_text('#!/bin/sh\nprintf "%s|%s|%s\\n" "$0" "$PWD" "$*" >> "$CALL_LOG"\n')
                mock.chmod(0o755)
            env = dict(os.environ, PATH=str(tools) + os.pathsep + os.environ["PATH"], CALL_LOG=str(log))
            result = subprocess.run(["bash", str(root / "scripts" / "build-all.sh")], cwd=work,
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            calls = log.read_text().splitlines()
            self.assertEqual(len(calls), 4)
            self.assertEqual([line.split("|", 2)[2] for line in calls],
                             ["clean", "iso", "scripts/inspect_img.py out/novus.img", "scripts/check_rootfs.py out"])
            self.assertTrue(all(line.split("|", 2)[1] == str(root) for line in calls))


if __name__ == "__main__":
    unittest.main()
