"""Regression tests for the kernel rebuild helper's checkout selection."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("rebuild-kernel.sh")


class RebuildKernelTests(unittest.TestCase):
    def test_runs_from_another_directory_with_spaces_in_checkout_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "checkout with spaces"
            (root / "scripts").mkdir(parents=True)
            (root / "out").mkdir()
            (root / "build").mkdir()
            (root / "bin").mkdir()
            script = root / "scripts" / "rebuild-kernel.sh"
            script.write_bytes(SCRIPT.read_bytes())
            (root / "scripts" / "font_smoke.sh").write_text("#!/bin/bash\nexit 0\n")
            make = root / "bin" / "make"
            make.write_text("#!/bin/sh\npwd > build/rebuild-cwd.txt\ntouch out/novus-live.iso\n")
            make.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = str(root / "bin") + os.pathsep + env.get("PATH", "")
            result = subprocess.run(["bash", str(script)], cwd=tmp, env=env,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual((root / "build" / "rebuild-cwd.txt").read_text().strip(), str(root))
            self.assertTrue((root / "out" / "novus-live.iso").is_file())


if __name__ == "__main__":
    unittest.main()
