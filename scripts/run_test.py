"""Host-side regression tests for scripts/run.sh ESP staging and QEMU arguments.

Run with: python3 -m unittest discover -s scripts -p run_test.py
"""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name('run.sh')


class RunTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'scripts').mkdir()
        (self.root / 'out').mkdir()
        (self.root / 'bin').mkdir()
        self.runner = self.root / 'scripts' / 'run.sh'
        shutil.copyfile(SCRIPT, self.runner)
        self.runner.chmod(0o755)
        self.args = self.root / 'qemu.args'
        qemu = self.root / 'bin' / 'qemu-system-x86_64'
        qemu.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$MOCK_QEMU_ARGS"\n')
        qemu.chmod(0o755)
        self.env = dict(os.environ, PATH=str(self.root / 'bin') + os.pathsep + os.environ['PATH'],
                        MOCK_QEMU_ARGS=str(self.args), DISPLAY='')

    def run_script(self, mem='4G', **env):
        return subprocess.run([str(self.runner), mem], cwd=self.root,
                              env=dict(self.env, **env), capture_output=True, text=True)

    def test_missing_esp_fails_before_qemu(self):
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('out/esp.img not found', result.stderr)
        self.assertFalse(self.args.exists())

    def test_full_esp_boots_read_only_snapshot_and_preserves_image(self):
        image = self.root / 'out' / 'esp.img'
        image.write_bytes(b'ESP fixture')
        (self.root / 'out' / 'OVMF_VARS.fd').write_bytes(b'OVMF fixture')
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        argv = self.args.read_text().splitlines()
        self.assertIn('if=ide,format=raw,file=out/esp.img,snapshot=on', argv)
        self.assertNotIn('format=raw,file=fat:rw:esp', argv)
        self.assertEqual(image.read_bytes(), b'ESP fixture')
        self.assertEqual(argv[argv.index('-m') + 1], '4G')
        self.assertEqual(argv[argv.index('-display') + 1], 'none')
        self.assertEqual(argv[argv.index('-device') + 1], 'e1000,netdev=novusnet')

    def test_custom_memory_nic_and_display(self):
        (self.root / 'out' / 'esp.img').write_bytes(b'ESP fixture')
        (self.root / 'out' / 'OVMF_VARS.fd').write_bytes(b'OVMF fixture')
        result = self.run_script('3G', DISPLAY=':0', NOVUS_NIC='virtio-net-pci')
        self.assertEqual(result.returncode, 0, result.stderr)
        argv = self.args.read_text().splitlines()
        self.assertEqual(argv[argv.index('-m') + 1], '3G')
        self.assertEqual(argv[argv.index('-display') + 1], 'gtk')
        self.assertEqual(argv[argv.index('-device') + 1], 'virtio-net-pci,netdev=novusnet')


if __name__ == '__main__':
    unittest.main()
