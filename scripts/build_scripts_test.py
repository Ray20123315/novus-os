"""Check that build helpers work from outside the checkout directory."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parent


class BuildScriptTests(unittest.TestCase):
    def check_script(self, name, expected):
        with tempfile.TemporaryDirectory(prefix="novus build path ") as temp:
            root = Path(temp) / "checkout with spaces"
            scripts = root / "scripts"
            scripts.mkdir(parents=True)
            shutil.copyfile(SCRIPTS / name, scripts / name)
            (root / "out").mkdir()
            (root / "build" / "tools").mkdir(parents=True)
            bin_dir = Path(temp) / "bin"
            bin_dir.mkdir()
            for executable in ("make", "python3"):
                stub = bin_dir / executable
                stub.write_text('#!/bin/sh\nprintf "%s:%s:%s\\n" "$PWD" "$0" "$*" >> "$NOVUS_TEST_LOG"\n')
                stub.chmod(0o755)
            log = Path(temp) / "commands.log"
            env = dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}", NOVUS_TEST_LOG=str(log))
            result = subprocess.run(["bash", str(scripts / name)], cwd=temp,
                                    env=env, text=True, capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            commands = [line.split(':', 2)[2] for line in log.read_text().splitlines()]
            self.assertEqual(commands, expected)
            self.assertTrue(all(line.startswith(str(root) + ':') for line in log.read_text().splitlines()))

    def test_full_build_from_other_directory(self):
        self.check_script("build-all.sh", ["clean", "iso", "scripts/inspect_img.py out/novus.img", "scripts/check_rootfs.py out"])

    def test_image_build_from_other_directory(self):
        self.check_script("build-img.sh", ["out/novus.img", "scripts/inspect_img.py out/novus.img"])


if __name__ == "__main__":
    unittest.main()
