"""Regression tests for the live ISO runner's optional disk argument."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("run-iso.sh")


class RunIsoDiskPathTests(unittest.TestCase):
    def test_relative_disk_is_resolved_from_invoking_directory(self):
        with tempfile.TemporaryDirectory(prefix="novus iso test ") as temp:
            root = Path(temp)
            checkout = root / "checkout with spaces"
            (checkout / "scripts").mkdir(parents=True)
            (checkout / "out").mkdir()
            (checkout / "out" / "novus-live.iso").touch()
            (checkout / "out" / "OVMF_VARS.fd").touch()
            runner = checkout / "scripts" / "run-iso.sh"
            runner.write_bytes(SCRIPT.read_bytes())
            caller = root / "caller with spaces"
            caller.mkdir()
            disk = caller / "target disk.img"
            disk.touch()
            bindir = root / "bin"
            bindir.mkdir()
            fake_qemu = bindir / "qemu-system-x86_64"
            fake_qemu.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
            fake_qemu.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = str(bindir) + os.pathsep + env["PATH"]
            env.pop("DISPLAY", None)
            result = subprocess.run(
                ["bash", str(runner), "4G", "target disk.img"],
                cwd=caller, env=env, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"format=raw,file={disk},if=ide", result.stdout.splitlines())


if __name__ == "__main__":
    unittest.main()
