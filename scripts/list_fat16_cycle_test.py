import pathlib
import subprocess
import sys
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).with_name('list_fat16.py')
STUB = '''class FatFS:
    def __init__(self, data):
        self.bps=512; self.spc=1; self.res=1; self.nf=2; self.fat_sz=1
        self.cycle=data==b'cycle'
    def entries(self, cluster):
        if cluster==0: return [(b'SUB        ',2,0,True)]
        if cluster==2:
            return [(b'LOOP       ',2,0,True)] if self.cycle else [(b'FILE    TXT',0,5,False)]
        return []
'''

class FatDirectoryCycleTests(unittest.TestCase):
    def run_image(self, contents):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            scripts = root / 'scripts'
            scripts.mkdir()
            (scripts / 'list_fat16.py').write_bytes(SCRIPT.read_bytes())
            (scripts / 'novusimg.py').write_text(STUB, encoding='utf-8')
            path = root / 'esp.img'
            path.write_bytes(contents)
            return subprocess.run([sys.executable, str(scripts / 'list_fat16.py'), str(path)], capture_output=True, text=True, timeout=5)

    def test_self_referential_directory_reports_error(self):
        result = self.run_image(b'cycle')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('directory cluster cycle', result.stderr)
        self.assertNotIn('RecursionError', result.stderr)

    def test_normal_nested_directory(self):
        result = self.run_image(b'normal')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('/SUB/FILE.TXT', result.stdout)
        self.assertIn('2 entries', result.stdout)

if __name__ == '__main__':
    unittest.main()
