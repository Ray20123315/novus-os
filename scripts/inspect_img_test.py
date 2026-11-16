"""Regression tests for recursive NovusFS image inspection."""
import runpy
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).with_name('inspect_img.py')


class FakeNovusFS:
    root = 1
    bs = 4096
    itbl = 2
    graph = {}

    def __init__(self, data):
        pass

    def dirents(self, ino):
        return self.graph.get(ino, ())

    def inode(self, ino):
        return {'mode': 2 if ino in self.graph else 1}


class InspectImageTests(unittest.TestCase):
    def run_inspector(self, graph):
        FakeNovusFS.graph = graph
        fake_module = types.ModuleType('novusimg')
        fake_module.NovusFS = FakeNovusFS
        fake_module.u32 = lambda *args: 0
        fake_module.u64 = lambda *args: 0
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / 'disk.img'
            image.write_bytes(b'placeholder')
            with patch.dict(sys.modules, {'novusimg': fake_module}), \
                 patch.object(sys, 'argv', [str(SCRIPT), str(image)]):
                runpy.run_path(str(SCRIPT), run_name='__main__')

    def test_acyclic_tree(self):
        self.run_inspector({1: [(2, 'a')], 2: [(3, 'file')]})

    def test_cycle_back_to_root(self):
        with self.assertRaisesRegex(ValueError, 'directory cycle'):
            self.run_inspector({1: [(2, 'a')], 2: [(1, 'back')]})

    def test_self_cycle(self):
        with self.assertRaisesRegex(ValueError, 'directory cycle'):
            self.run_inspector({1: [(1, 'self')]})

    def test_shared_directory_without_cycle(self):
        self.run_inspector({1: [(2, 'a'), (3, 'b')], 2: [(4, 'shared')],
                            3: [(4, 'shared')], 4: []})


if __name__ == '__main__':
    unittest.main()
