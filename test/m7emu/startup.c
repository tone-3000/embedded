/* Bare-metal startup for running the Cortex-M7 engines under emulation
 * (m7emu.py). Not for real hardware. Writing 1 to EMU_DONE ends the run. */
#include <stdint.h>

#define EMU_DONE (*(volatile uint32_t*)0x40000000)

extern int main(void);
extern void __libc_init_array(void);

__attribute__((naked, section(".vectors"))) void _start(void)
{
    __asm__ volatile(
        "ldr sp, =__stack_top\n\t"
        /* CPACR: enable CP10/CP11 (FPU) */
        "ldr r0, =0xE000ED88\n\t"
        "ldr r1, [r0]\n\t"
        "orr r1, r1, #(0xF << 20)\n\t"
        "str r1, [r0]\n\t"
        "dsb\n\t"
        "isb\n\t"
        "bl __libc_init_array\n\t"
        "bl main\n\t"
        "ldr r0, =0x40000000\n\t"
        "mov r1, #1\n\t"
        "str r1, [r0]\n\t"
        "b .\n\t");
}

void _init(void) {}
void _fini(void) {}
void* __dso_handle = 0;
