"""Host-side regression tests for PS/2 IRQ registration in nd_input_init.

Compiles the actual initializer extracted from graphics/nd_input.c against
an I/O and IRQ stub. This tests controller configuration and rollback policy,
not delivery of hardware interrupts or real PS/2 devices.
"""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def extract_initializer(source):
    marker = "void nd_input_init(void) {"
    begin = source.index(marker)
    depth = 0
    for i in range(begin + len(marker) - 1, len(source)):
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
            if depth == 0:
                return source[begin:i + 1]
    raise ValueError("nd_input_init function body is incomplete")


PREFIX = r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef uint8_t UINT8;
typedef uint32_t UINT32;
typedef int32_t INT32;
typedef struct { int available; UINT32 width, height; } nd_display_t;
#define PS2_DATA 0x60
#define PS2_CMD_WRITE_CFG 0x60
#define PS2_CMD_DISABLE_K 0xAD
#define PS2_CMD_DISABLE_M 0xA7
#define PS2_CMD_ENABLE_K 0xAE
#define PS2_CMD_ENABLE_M 0xA8
#define PS2_CMD_READ_CFG 0x20
#define PS2_CMD_NEXT_MOUSE 0xD4
#define ND_RAW_QUEUE 256
static UINT32 g_head, g_tail, g_raw_head, g_raw_tail, g_raw_dropped;
static UINT8 g_irq_logged, g_mouse_bytes, g_extended, g_shift, g_caps;
static UINT8 g_ctrl, g_buttons;
static INT32 g_mx, g_my;
static int cfg_available, result_kbd, result_mouse;
static int reg_kbd, reg_mouse, unreg_kbd, unreg_mouse;
static int cfg_writes, config_pending, dis_kbd, dis_mouse, vm_inits;
static UINT8 last_cfg;
static const nd_display_t *nd_display(void) { return NULL; }
static void ps2_cmd(UINT8 cmd) {
    if (cmd == PS2_CMD_WRITE_CFG) config_pending = 1;
    if (cmd == PS2_CMD_DISABLE_K) dis_kbd++;
    if (cmd == PS2_CMD_DISABLE_M) dis_mouse++;
}
static void ps2_write(UINT8 value) {
    if (config_pending) { last_cfg = value; cfg_writes++; config_pending = 0; }
}
static void ps2_flush(void) {}
static int ps2_wait_out(void) { return cfg_available; }
static UINT8 io_in8(UINT8 port) { (void)port; return 0x40; }
static void ps2_irq(void *ctx) { (void)ctx; }
static int irq_register(UINT32 line, UINT32 flags, void (*handler)(void *),
                        void *ctx, const char *name) {
    (void)flags; (void)handler; (void)ctx; (void)name;
    if (line == 1) { reg_kbd++; return result_kbd ? 32 : -1; }
    if (line == 12) { reg_mouse++; return result_mouse ? 33 : -1; }
    return -1;
}
int irq_unregister(UINT32 line, void (*handler)(void *), void *ctx) {
    (void)handler; (void)ctx;
    if (line == 1) unreg_kbd++;
    if (line == 12) unreg_mouse++;
    return 0;
}
static void kputs(const char *s) { (void)s; }
static void vm_mouse_init(void) { vm_inits++; }
'''

SUFFIX = r'''
int main(int argc, char **argv) {
    int mode;
    UINT8 expected_cfg;
    if (argc != 2) return 99;
    mode = atoi(argv[1]);
    cfg_available = (mode != 4);
    result_kbd = (mode == 0 || mode == 1);
    result_mouse = (mode == 0 || mode == 2);
    nd_input_init();
    if (vm_inits != 1) return 98;
    if (mode == 4) {
        if (reg_kbd || reg_mouse || cfg_writes) return 97;
        return 0;
    }
    if (reg_kbd != 1 || reg_mouse != 1) return 1;
    if (unreg_kbd || unreg_mouse) return 2;
    if (cfg_writes != 2) return 3;
    expected_cfg = (UINT8)(0x40 | (result_kbd ? 0x01 : 0x10) |
                            (result_mouse ? 0x02 : 0x20));
    if (last_cfg != expected_cfg) {
        fprintf(stderr, "expected config 0x%02x got 0x%02x\n",
                expected_cfg, last_cfg);
        return 4;
    }
    if (!result_kbd && dis_kbd < 2) return 5;
    if (!result_mouse && dis_mouse < 2) return 6;
    return 0;
}
'''


class PS2IndependentIRQTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which("cc") is None:
            raise unittest.SkipTest("C compiler not available")
        cls.tmp = tempfile.TemporaryDirectory()
        source = (ROOT / "graphics" / "nd_input.c").read_text(encoding="utf-8")
        generated = Path(cls.tmp.name) / "ps2_irq_harness.c"
        generated.write_text(PREFIX + extract_initializer(source) + SUFFIX,
                             encoding="utf-8")
        cls.binary = Path(cls.tmp.name) / "ps2_irq_harness"
        subprocess.run(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                        str(generated), "-o", str(cls.binary)],
                       check=True, capture_output=True, text=True)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "tmp"):
            cls.tmp.cleanup()

    def check_case(self, mode):
        result = subprocess.run([str(self.binary), str(mode)],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr or
                         f"harness returned {result.returncode}")

    def test_both_irq_lines_work(self):
        self.check_case(0)

    def test_keyboard_survives_mouse_irq_failure(self):
        self.check_case(1)

    def test_mouse_survives_keyboard_irq_failure(self):
        self.check_case(2)

    def test_both_irq_lines_fail(self):
        self.check_case(3)

    def test_controller_configuration_unavailable(self):
        self.check_case(4)


if __name__ == "__main__":
    unittest.main()
