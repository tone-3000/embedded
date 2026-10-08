/* Cortex-M7 emulation harness: runs one model over the test input with the
 * engines' Cortex-M7 assembly, as on a board. m7emu.py loads the ELF, writes
 * emu_cfg and emu_in, runs it and checks emu_out against the reference. */
#include <stdint.h>
#include <string.h>

#include "a2_engine.h"

/* Both captures, verbatim (the Makefile sets the paths). */
__asm__(".section .rodata.emu_namb,\"a\",%progbits\n"
        ".balign 4\n"
        "emu_namb_a2lite:\n"
        ".incbin \"" EMU_NAMB_A2LITE "\"\n"
        "emu_namb_a2lite_end:\n"
        ".balign 4\n"
        "emu_namb_a2full:\n"
        ".incbin \"" EMU_NAMB_A2FULL "\"\n"
        "emu_namb_a2full_end:\n"
        ".previous\n");
extern const uint8_t emu_namb_a2lite[], emu_namb_a2lite_end[], emu_namb_a2full[], emu_namb_a2full_end[];

#define EMU_MAX_SAMPLES 96000

/* Written by m7emu.py before the run. block: frames per call, 0 = sizes that
 * change on every call (1..A2_MAX_FRAMES). */
volatile struct {
    uint32_t model; /* 1 = A2-Lite, 2 = A2-Full */
    uint32_t block;
    uint32_t n;
    int32_t status; /* written by the harness: 0 = ran, < 0 = error */
} emu_cfg;
float emu_in[EMU_MAX_SAMPLES];
float emu_out[EMU_MAX_SAMPLES];

int main(void)
{
    const int full = emu_cfg.model == 2;
    const uint8_t* namb = full ? emu_namb_a2full : emu_namb_a2lite;
    const uint32_t size = (uint32_t)((full ? emu_namb_a2full_end : emu_namb_a2lite_end) - namb);
    const char* err;
    if (emu_cfg.n > EMU_MAX_SAMPLES || a2_load(namb, size, 1, &err) != 0
        || a2_model() != (full ? A2_FULL : A2_LITE)) {
        emu_cfg.status = -1;
        return 0;
    }
    unsigned rng = 12345u;
    for (uint32_t s = 0; s < emu_cfg.n;) {
        int k = (int)emu_cfg.block;
        if (k == 0) {
            rng = rng * 1103515245u + 12345u;
            k = 1 + (int)((rng >> 16) % A2_MAX_FRAMES);
        }
        if (k > (int)(emu_cfg.n - s))
            k = (int)(emu_cfg.n - s);
        a2_process(&emu_in[s], &emu_out[s], k);
        s += (uint32_t)k;
    }
    emu_cfg.status = 0;
    return 0;
}
