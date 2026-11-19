"""Regression coverage for comma-containing QEMU disk image filenames."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("run-iso.sh")


class RunIsoCommaTest(unittest.TestCase):
    def test_disk_filename_commas_are_escaped_for_qemu_drive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "checkout"
            (root / "scripts").mkdir(parents=True)
            (root / "out").mkdir()
            (root / "out/novus-live.iso").touch()
            (root / "out/OVMF_VARS.fd").touch()
            disk = root / "disk,backup.img"
            disk.touch()
            script = root / "scripts/run-iso.sh"
            script.write_bytes(SCRIPT.read_bytes())
            fake_bin = Path(tmp) / "bin"
            fake_bin.mkdir()
            fake_qemu = fake_bin / "qemu-system-x86_64"
            fake_qemu.write_text(
                "#!/usr/bin/env python3\n"
                "import json, sys\n"
                "print(json.dumps(sys.argv[1:]))\n",
                encoding="utf-8",
            )
            fake_qemu.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")
            env.pop("DISPLAY", None)
            proc = subprocess.run(
                ["bash", str(script), "4G", str(disk)],
                cwd=tmp, env=env, capture_output=True, text=True,
                check=True,
            )
            args = json.loads(proc.stdout)
            drives = [args[i + 1] for i, arg in enumerate(args[:-1])
                      if arg == "-drive"]
            self.assertIn(
                "format=raw,file=%s,if=ide" % str(disk).replace(",", ",,"),
                drives,
            )


if __name__ == "__main__":
    unittest.main()
