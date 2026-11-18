"""Regression tests for build helper PATH preservation."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPTS = ('build-all.sh', 'build-img.sh')
ROOT = Path(__file__).resolve().parent.parent


class BuildHelperPathTests(unittest.TestCase):
    def test_helpers_preserve_caller_path(self):
        for name in SCRIPTS:
            with self.subTest(script=name), tempfile.TemporaryDirectory() as tmp:
                tmpdir = Path(tmp)
                for command in ('make', 'python3'):
                    stub = tmpdir / command
                    stub.write_text('#!/bin/sh\nprintf "%s\\n" "$PATH" >> "$PATH_LOG"\n')
                    stub.chmod(0o755)
                log = tmpdir / 'path.log'
                env = os.environ.copy()
                env.update(PATH=f'{tmpdir}:/usr/bin:/bin', PATH_LOG=str(log), TEST_ROOT=str(tmpdir))
                # The existing fixed checkout path is unrelated to this test.
                # Override only cd; execute the actual helper script unchanged.
                shell = 'cd() { builtin cd "$TEST_ROOT"; }; export -f cd; bash "$1"'
                result = subprocess.run(
                    ['bash', '-c', shell, 'bash', str(ROOT / 'scripts' / name)],
                    env=env, capture_output=True, text=True, timeout=10,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(log.exists())
                self.assertEqual(set(log.read_text().splitlines()), {env['PATH']})


if __name__ == '__main__':
    unittest.main()
