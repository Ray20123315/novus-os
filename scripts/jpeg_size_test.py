#!/usr/bin/env python3
"""Host regression for the production JPEG dimension parser (no OS boot required)."""
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = ROOT / "graphics" / "nd_jpeg.c"


class JpegSizeTest(unittest.TestCase):
    def test_marker_lengths(self):
        cc = shutil.which("cc")
        if cc is None:
            self.skipTest("host C compiler unavailable")
        source = SOURCE.read_text(encoding="utf-8")
        start = source.index("int nd_jpeg_size(")
        end = source.index("int nd_jpeg_decode(", start)
        function = source[start:end]
        harness = r'''
#include <stdint.h>
#include <stddef.h>
typedef uint8_t UINT8;
typedef uint16_t UINT16;
typedef uint32_t UINT32;
static UINT16 jp_be16(const UINT8 *p) { return (UINT16)(((UINT16)p[0] << 8) | p[1]); }
''' + function + r'''
#define CHECK(expected, ...) do { \
  const UINT8 b[] = {__VA_ARGS__}; int w = -1, h = -1; \
  if (nd_jpeg_size(b, (UINT32)sizeof(b), &w, &h) != (expected)) return __LINE__; \
} while (0)
int main(void) {
  CHECK(0, 0xff,0xd8,0xff,0xc0,0,11,8,0,1,0,2,1,1,0,0xff,0xd9);
  CHECK(0, 0xff,0xd8,0xff,0xe0,0,2,0xff,0xc0,0,11,8,0,1,0,2,1,1,0,0xff,0xd9);
  CHECK(-1, 0xff,0xd8,0xff,0xe0,0,0,0xff,0xc0,0,11,8,0,1,0,2,1,1,0,0xff,0xd9);
  CHECK(-1, 0xff,0xd8,0xff,0xe0,0,1,0xff,0xc0,0,11,8,0,1,0,2,1,1,0,0xff,0xd9);
  CHECK(-1, 0xff,0xd8,0xff,0xe0,0,50,0xff,0xc0,0,11,8,0,1,0,2,1,1,0,0xff,0xd9);
  CHECK(-1, 0xff,0xd8,0xff,0xc0,0,2,8,0,1,0,2,1,1,0,0xff,0xd9);
  CHECK(-1, 0xff,0xd8,0xff,0xc0,0,11,8,0,1);
  return 0;
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            c = pathlib.Path(tmp) / "test.c"
            exe = pathlib.Path(tmp) / "test"
            c.write_text(harness, encoding="utf-8")
            subprocess.run([cc, "-std=gnu11", "-Wall", "-Wextra", "-Werror",
                            "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                            str(c), "-o", str(exe)], check=True)
            subprocess.run([str(exe)], check=True)


if __name__ == "__main__":
    unittest.main()
