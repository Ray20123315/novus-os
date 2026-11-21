"""Regression for the required ISO primary ESP.IMG entry."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent


class IsoEspImageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        scripts = root / 'scripts'
        scripts.mkdir()
        shutil.copyfile(HERE / 'check_rootfs.py', scripts / 'check_rootfs.py')
        (scripts / 'novusimg.py').write_text('''\
class NovusFS:
    def __init__(self, data):
        pass
    def is_dir(self, path):
        return True
    def lookup(self, path):
        return 1
    def read_file(self, path):
        return b'font' if path == 'Novus/fonts/font.bin' else b'fstype=novusfs'

class FatFS:
    def __init__(self, data):
        pass
    def is_dir(self, path):
        return True
    def read_file(self, path):
        return b'fstype=novusfs'

class IsoFS:
    def __init__(self, data):
        self.has_esp = data == b'has-esp'
        self.trees = {'joliet': object(), 'primary': object()}
    def is_dir(self, path, tree):
        return True
    def lookup(self, path, tree):
        if tree == 'primary' and path == 'ESP.IMG' and not self.has_esp:
            return None
        return object()
    def read_file(self, path, tree):
        return b'fstype=novusfs'
''', encoding='utf-8')
        layout = root / 'fs' / 'novusfs'
        layout.mkdir(parents=True)
        (layout / 'rootfs_layout.h').write_text(
            '#define NOVUS_LAYOUT_DIRS(X)\\\n' +
            ''.join('X("Dir%02d", "D%02d", 0)\\\n' % (n, n) for n in range(77)) +
            '/* Number of directory entries */\n' +
            '#define NOVUS_LAYOUT_META(X)\n' +
            '#define NOVUS_LAYOUT_MOUNTS(X)\n' +
            '#endif\n', encoding='utf-8')
        graphics = root / 'graphics'
        graphics.mkdir()
        (graphics / 'nd_font_data.bin').write_bytes(b'font')
        self.out = root / 'out'
        self.out.mkdir()
        for name in ('novus.img', 'esp-tpl.img', 'esp.img'):
            (self.out / name).write_bytes(b'fixture')
        self.checker = scripts / 'check_rootfs.py'

    def run_checker(self, iso_payload):
        (self.out / 'novus-live.iso').write_bytes(iso_payload)
        return subprocess.run([sys.executable, str(self.checker), str(self.out)],
                              cwd=self.tmp.name, text=True, capture_output=True,
                              check=False)

    def test_primary_esp_image_present(self):
        result = self.run_checker(b'has-esp')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_primary_esp_image_missing(self):
        result = self.run_checker(b'no-esp')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('ISO primary: ESP.IMG missing', result.stdout)


if __name__ == '__main__':
    unittest.main()
