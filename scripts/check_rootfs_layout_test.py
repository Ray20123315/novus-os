"""Regression tests for the root layout count guard, including python -O."""
import ast
from pathlib import Path
import subprocess
import sys
import unittest

SCRIPT = Path(__file__).with_name('check_rootfs.py')


def layout_guard():
    source = SCRIPT.read_text(encoding='utf-8')
    tree = ast.parse(source)
    for index, node in enumerate(tree.body):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == 'DIRS'
            for target in node.targets
        ):
            return ast.get_source_segment(source, tree.body[index + 1])
    raise AssertionError('DIRS assignment not found')


class LayoutCountTests(unittest.TestCase):
    def check_count(self, count, optimized):
        code = f'DIRS = [None] * {count}\n{layout_guard()}\n'
        command = [sys.executable]
        if optimized:
            command.append('-O')
        return subprocess.run(command + ['-c', code], capture_output=True, text=True)

    def test_expected_count(self):
        for optimized in (False, True):
            with self.subTest(optimized=optimized):
                self.assertEqual(self.check_count(77, optimized).returncode, 0)

    def test_changed_count_rejected(self):
        for optimized in (False, True):
            with self.subTest(optimized=optimized):
                result = self.check_count(76, optimized)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('layout directory count changed: 76', result.stderr)


if __name__ == '__main__':
    unittest.main()
