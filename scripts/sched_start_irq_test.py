"""Check the first ring-3 handoff cannot be interrupted halfway through.

The C harness compiles the actual sched_start() body extracted from sched.c.
Only the privileged CLI instruction is replaced by a host-side IRQ flag, so
it can execute under a normal user process. This is NOT a hardware IRQ test.
"""

from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def function_body(text, signature):
    start = text.index(signature)
    opening = text.index('{', start)
    level = 0
    for end in range(opening, len(text)):
        if text[end] == '{':
            level += 1
        elif text[end] == '}':
            level -= 1
            if level == 0:
                return text[start:end + 1]
    raise ValueError('unterminated function')


HARNESS_PREFIX = r'''
#include <setjmp.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

typedef uint64_t UINT64;
typedef struct {
  int state;
  uint32_t slice;
  UINT64 kstack_top, cr3, teb_va, rsp;
  const char *name;
} task_t;
#define TASK_RUNNING 2
#define MSR_FS_BASE 0xC0000100u

static jmp_buf end_test;
static int interrupts_enabled = 1;
static int order_error;
static int pick_none;
static int finished;
static task_t task = {0, 0, 0x1000u, 0x2000u, 0x3000u, 0x4000u, "idle"};
static task_t *g_current;
static int g_sched_started;
static UINT64 sys_kernel_rsp;

static void fake_cli(void) __attribute__((unused));
static void fake_cli(void) { interrupts_enabled = 0; }
static void verify_irqs_off(void) {
  if (interrupts_enabled) order_error = 1;
}
static task_t *task_pick_next(void) {
  verify_irqs_off();
  return pick_none ? NULL : &task;
}
static void kputs(const char *s) { (void)s; }
static uint32_t task_slice(const task_t *t) { (void)t; return 4u; }
static void tss_set_rsp0(UINT64 rsp) {
  verify_irqs_off();
  if (rsp != task.kstack_top || !g_sched_started) order_error = 2;
}
static void vm_switch_cr3(UINT64 cr3) {
  verify_irqs_off();
  if (cr3 != task.cr3 || g_current != &task) order_error = 3;
}
static void msr_write(UINT64 reg, UINT64 value) {
  verify_irqs_off();
  if (reg != MSR_FS_BASE || value != task.teb_va) order_error = 4;
}
static void sched_enter(UINT64 frame) __attribute__((noreturn));
static void sched_enter(UINT64 frame) {
  verify_irqs_off();
  if (frame != task.rsp || task.state != TASK_RUNNING ||
      task.slice != 4u || sys_kernel_rsp != task.kstack_top)
    order_error = 5;
  finished = 1;
  longjmp(end_test, 1);
}
static void cpu_halt(void) {
  verify_irqs_off();
  finished = 2;
  longjmp(end_test, 1);
}
'''

HARNESS_SUFFIX = r'''
int main(int argc, char **argv) {
  if (argc != 2) return 90;
  pick_none = atoi(argv[1]);
  if (setjmp(end_test) == 0) sched_start();
  if (order_error) {
    fprintf(stderr, "unsafe handoff: %d\n", order_error);
    return 1;
  }
  if (interrupts_enabled) return 2;
  if (finished != (pick_none ? 2 : 1)) return 3;
  return 0;
}
'''


class SchedulerStartIRQTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which('cc') is None:
            raise unittest.SkipTest('Host C compiler unavailable')
        source = (ROOT / 'kernel' / 'sched.c').read_text(encoding='utf-8')
        cls.source = source
        initializer = function_body(source, 'void sched_start(void)')
        # Execute the real function body. CLI cannot run in user mode;
        # instrument exactly that assembly instruction as a fake IRQ mask.
        initializer = initializer.replace(
            '__asm__ volatile("cli" ::: "memory");', 'fake_cli();')
        cls.tmp = tempfile.TemporaryDirectory()
        cls.program = Path(cls.tmp.name) / 'handoff'
        harness = Path(cls.tmp.name) / 'handoff.c'
        harness.write_text(HARNESS_PREFIX + initializer + HARNESS_SUFFIX,
                           encoding='utf-8')
        compile_result = subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                        '-O0', str(harness), '-o', str(cls.program)],
                       check=False, capture_output=True, text=True)
        if compile_result.returncode != 0:
            raise AssertionError(compile_result.stderr)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'tmp'):
            cls.tmp.cleanup()

    def run_mode(self, value):
        result = subprocess.run([str(self.program), str(value)],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0,
                         result.stderr or f'return code {result.returncode}')

    def test_live_task_enters_with_interrupts_masked(self):
        self.run_mode(0)

    def test_no_task_halts_with_interrupts_masked(self):
        self.run_mode(1)

    def test_first_user_frame_restores_interrupts(self):
        body = function_body(self.source, 'static void task_build_frame(')
        self.assertRegex(body, r'f->rflags\s*=\s*0x202u\s*;')


if __name__ == '__main__':
    unittest.main()
