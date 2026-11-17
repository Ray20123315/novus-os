"""Regression checks for the font payload comparison in check_rootfs.py."""
import ast
from pathlib import Path
import unittest


class FontPayloadTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = Path(__file__).with_name('check_rootfs.py').read_text(encoding='utf-8')
        tree = ast.parse(source)
        matches = [node for node in ast.walk(tree)
                   if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                   and node.func.id == 'check' and len(node.args) == 2
                   and isinstance(node.args[1], ast.Constant)
                   and node.args[1].value == 'novus.img: font payload mismatch']
        assert len(matches) == 1, 'expected exactly one font payload check'
        cls.condition = compile(ast.Expression(matches[0].args[0]), '<font check>', 'eval')

    def matches(self, font, ref):
        return eval(self.condition, {'__builtins__': {}}, {'font': font, 'ref': ref})

    def test_identical_font(self):
        self.assertTrue(self.matches(b'\\x00font\\xff', b'\\x00font\\xff'))

    def test_different_font(self):
        self.assertFalse(self.matches(b'font-A', b'font-B'))

    def test_missing_font(self):
        self.assertFalse(self.matches(None, b'font'))

    def test_empty_font(self):
        self.assertTrue(self.matches(b'', b''))

    def test_comparison_does_not_depend_on_hash(self):
        self.assertFalse(self.matches(b'different-A', b'different-B'))


if __name__ == '__main__':
    unittest.main()
