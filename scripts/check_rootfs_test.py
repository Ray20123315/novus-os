"""Regression tests for exact rootfs metadata validation."""
import ast
import json
import os
import unittest


SOURCE = os.path.join(os.path.dirname(__file__), 'check_rootfs.py')
with open(SOURCE, encoding='utf-8') as source:
    tree = ast.parse(source.read(), filename=SOURCE)
func = next(node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == 'check_meta')
namespace = {'json': json, 'MOUNTS': [
    '/', '/disk0', '/disk1', '/media/cdrom0', '/media/usb0', '/media/usb1']}
exec(compile(ast.Module(body=[func], type_ignores=[]), SOURCE, 'exec'), namespace)


class RootfsMetadataTest(unittest.TestCase):
    def setUp(self):
        self.errors = []
        namespace['check'] = lambda condition, message: (
            self.errors.append(message) if not condition else None)

    def check_meta(self, data, expect_mounts=True):
        namespace['check_meta'](data, 'fixture', expect_mounts)
        return self.errors

    def mounts(self, paths=None, root_fstype='novusfs'):
        if paths is None:
            paths = namespace['MOUNTS']
        return ('\n'.join(json.dumps({
            'path': path,
            'fstype': root_fstype if path == '/' else 'auto'
        }) for path in paths) + '\n').encode('ascii')

    def test_valid_fsinfo(self):
        self.assertFalse(self.check_meta(
            b'volume=NOVUS_SYSTEM\nfstype=novusfs\n', False))

    def test_fsinfo_substring_is_not_a_field(self):
        self.assertTrue(self.check_meta(b'not_fstype=novusfs\n', False))

    def test_valid_mounts(self):
        self.assertFalse(self.check_meta(self.mounts()))

    def test_mount_path_prefix_is_not_a_match(self):
        paths = ['/' if p == '/' else p + '-wrong'
                 for p in namespace['MOUNTS']]
        self.assertTrue(any('missing mount path' in error for error
                            in self.check_meta(self.mounts(paths))))

    def test_root_requires_novusfs_fstype(self):
        self.assertTrue(any('bad metadata' in error for error
                            in self.check_meta(self.mounts(root_fstype='auto'))))

    def test_invalid_json_is_rejected(self):
        self.assertTrue(self.check_meta(b'{not json}\n'))


if __name__ == '__main__':
    unittest.main()
