"""Regression tests for required live ESP boot-stage payloads."""

import unittest

from live_esp_checks import check_live_esp_payloads


class FakeFat:
    def __init__(self, files):
        self.files = files

    def read_file(self, path):
        return self.files.get(path)


class LiveEspChecksTests(unittest.TestCase):
    def run_checks(self, files):
        results = []
        check_live_esp_payloads(FakeFat(files), lambda ok, msg: results.append((ok, msg)))
        return results

    def test_valid_live_esp(self):
        self.assertEqual(self.run_checks({'ESP.IMG': b'fat image', 'TEST.NKM': b'signed module'}),
                         [(True, 'esp.img: missing or empty ESP.IMG'),
                          (True, 'esp.img: missing or empty TEST.NKM')])

    def test_missing_installer_template(self):
        results = self.run_checks({'TEST.NKM': b'signed module'})
        self.assertEqual(results[0], (False, 'esp.img: missing or empty ESP.IMG'))
        self.assertTrue(results[1][0])

    def test_empty_signed_module(self):
        results = self.run_checks({'ESP.IMG': b'fat image', 'TEST.NKM': b''})
        self.assertTrue(results[0][0])
        self.assertEqual(results[1], (False, 'esp.img: missing or empty TEST.NKM'))


if __name__ == '__main__':
    unittest.main()
