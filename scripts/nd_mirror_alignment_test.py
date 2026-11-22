"""Host-side regression for 1:1 mirrors with centered letterboxing.

Compile the actual map_of() and nd_mirror_rect() implementation from nd_hal.c
with fake framebuffer surfaces. No GPU or real hardware access is needed.
"""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def c_function(source, start_marker):
    begin = source.index(start_marker)
    opening = source.index('{', begin)
    depth = 0
    for i in range(opening, len(source)):
        if source[i] == '{':
            depth += 1
        elif source[i] == '}':
            depth -= 1
            if depth == 0:
                return source[begin:i + 1]
    raise ValueError('unterminated C function')


C_PREFIX = r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef int32_t INT32;
typedef int64_t INT64;
typedef uint32_t UINT32;
typedef struct { INT32 x, y, w, h; } nd_rect_t;
typedef struct {
  UINT32 *px;
  INT32 w, h, stride;
  int fb, bgr;
} nd_surface_t;
static nd_surface_t g_source;
static nd_surface_t g_mirror[1];
static UINT32 g_mirror_count = 1;
static nd_rect_t nd_rect(INT32 x, INT32 y, INT32 w, INT32 h) {
  nd_rect_t r = {x, y, w, h}; return r;
}
static nd_surface_t *nd_canvas(void) { return &g_source; }
static int surface_swapped(const nd_surface_t *s) { return s->fb && !s->bgr; }
static UINT32 swap_rb(UINT32 px) {
  return (px & 0xFF00FF00u) | ((px & 0x000000FFu) << 16) |
         ((px & 0x00FF0000u) >> 16);
}
static void surface_copy(nd_surface_t *dst, const nd_surface_t *src, nd_rect_t r) {
  INT32 y;
  for (y = 0; y < r.h; y++) {
    memcpy(dst->px + (r.y + y) * dst->stride + r.x,
           src->px + (r.y + y) * src->stride + r.x, r.w * sizeof(UINT32));
  }
}

typedef struct {
  INT64 scale;
  INT32 off_x, off_y;
} nd_map_t;
'''

C_SUFFIX = r'''
static UINT32 image[4 * 2];
static UINT32 mirror[8 * 8];
static void init(INT32 dw, INT32 dh) {
  INT32 i;
  for (i = 0; i < 4 * 2; i++) image[i] = 0xFF000100u + (UINT32)i;
  for (i = 0; i < 8 * 8; i++) mirror[i] = 0xDDDDDDDDu;
  g_source = (nd_surface_t){image, 4, 2, 4, 0, 1};
  g_mirror[0] = (nd_surface_t){mirror, dw, dh, dw, 1, 1};
}
static int expect(INT32 x, INT32 y, UINT32 want) {
  UINT32 got = mirror[y * g_mirror[0].stride + x];
  if (got == want) return 0;
  fprintf(stderr,"pixel (%d,%d): got %#x expected %#x\n",x,y,got,want);
  return 1;
}
int main(int argc, char **argv) {
  int mode = argc > 1 ? atoi(argv[1]) : -1;
  int fail = 0;
  switch (mode) {
    case 0: /* Exactly matching dimensions: retain fast row copies */
      init(4, 2);
      nd_mirror_rect(nd_rect(0, 0, 4, 2));
      fail |= expect(0, 0, image[0]);
      fail |= expect(3, 1, image[7]);
      break;
    case 1: /* Same width; extra height needs top/bottom letterboxing */
      init(4, 4);
      nd_mirror_rect(nd_rect(0, 0, 4, 2));
      fail |= expect(0, 0, 0xFF10141Cu);
      fail |= expect(0, 1, image[0]);
      fail |= expect(3, 2, image[7]);
      fail |= expect(0, 3, 0xFF10141Cu);
      break;
    case 2: /* Same height; extra width needs left/right letterboxing */
      init(6, 2);
      nd_mirror_rect(nd_rect(0, 0, 4, 2));
      fail |= expect(0, 0, 0xFF10141Cu);
      fail |= expect(1, 0, image[0]);
      fail |= expect(4, 1, image[7]);
      fail |= expect(5, 0, 0xFF10141Cu);
      break;
    case 3: /* Damage must keep the same source-to-mirror offset */
      init(6, 2);
      nd_mirror_rect(nd_rect(2, 0, 2, 2));
      fail |= expect(2, 0, 0xDDDDDDDDu);
      fail |= expect(3, 0, image[2]);
      fail |= expect(4, 1, image[7]);
      fail |= expect(1, 0, 0xDDDDDDDDu);
      break;
    case 4: /* Actual scaled mirrors still use the general path */
      init(2, 2);
      nd_mirror_rect(nd_rect(0, 0, 4, 2));
      fail |= expect(0, 0, image[0]);
      fail |= expect(1, 0, image[2]);
      fail |= expect(0, 1, 0xFF10141Cu);
      break;
    case 5: /* RGB destination still needs color conversion with offset */
      init(6, 2);
      g_mirror[0].bgr = 0;
      image[0] = 0xFF112233u;
      nd_mirror_rect(nd_rect(0, 0, 4, 2));
      fail |= expect(1, 0, 0xFF332211u);
      fail |= expect(0, 0, 0xFF10141Cu);
      break;
    default: return 97;
  }
  return fail ? 1 : 0;
}
'''


class MirrorAlignmentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which('cc') is None:
            raise unittest.SkipTest('Host C compiler unavailable')
        source = (ROOT / 'graphics' / 'nd_hal.c').read_text(encoding='utf-8')
        cls.tmp = tempfile.TemporaryDirectory()
        cls.binary = Path(cls.tmp.name) / 'mirror'
        cfile = Path(cls.tmp.name) / 'mirror.c'
        cfile.write_text(C_PREFIX +
            c_function(source, 'static nd_map_t map_of(') + '\n' +
            c_function(source, 'void nd_mirror_rect(') + '\n' + C_SUFFIX,
            encoding='utf-8')
        result = subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                                 '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                                 str(cfile), '-o', str(cls.binary)],
                                capture_output=True, text=True, check=False)
        if result.returncode:
            raise AssertionError(result.stderr)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'tmp'):
            cls.tmp.cleanup()

    def check_case(self, n):
        proc = subprocess.run([str(self.binary), str(n)],
                              capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_equal_dimensions(self): self.check_case(0)
    def test_vertical_letterbox(self): self.check_case(1)
    def test_horizontal_letterbox(self): self.check_case(2)
    def test_partial_damage_offset(self): self.check_case(3)
    def test_scaled_mirror(self): self.check_case(4)
    def test_rgb_mirror_offset(self): self.check_case(5)


if __name__ == '__main__':
    unittest.main()
