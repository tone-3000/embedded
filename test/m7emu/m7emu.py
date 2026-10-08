#!/usr/bin/env python3
"""m7emu.py - run the Cortex-M7 engines' assembly under emulation and check
the output against the NeuralAmpModelerCore references.

    python3 m7emu.py build/emu.elf [build/emu-b16.elf ...]

Each ELF (built by the Makefile from emu_main.c) runs both models over
test/golden_input.raw at block 48, block 16 and block sizes that change on
every call. Unicorn emulates a Cortex-M7 with its FPU; it checks what the
code computes, not how fast (see the benchmarks for that). Needs
`pip install unicorn pyelftools`.
"""
import os
import struct
import sys
import time

from elftools.elf.elffile import ELFFile
from unicorn import Uc, UcError, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS, UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_PC, UC_CPU_ARM_CORTEX_M7

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RAM_BASE, RAM_SIZE = 0x20000000, 32 << 20
DONE_ADDR, SCS_BASE = 0x40000000, 0xE000E000
MODELS = {"a2lite": 1, "a2full": 2}


def load_elf(path):
    with open(path, "rb") as f:
        elf = ELFFile(f)
        segs = [(s["p_paddr"], s.data()) for s in elf.iter_segments() if s["p_type"] == "PT_LOAD" and s["p_filesz"]]
        syms = {s.name: s["st_value"] for s in elf.get_section_by_name(".symtab").iter_symbols()}
        return segs, syms, elf.header["e_entry"]


def run(segs, syms, entry, model, block, x):
    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
    uc.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_M7)
    uc.mem_map(RAM_BASE, RAM_SIZE)
    uc.mem_map(DONE_ADDR, 0x1000)
    uc.mem_map(SCS_BASE, 0x1000)
    for addr, data in segs:
        uc.mem_write(addr, data)
    uc.mem_write(syms["emu_cfg"], struct.pack("<IIIi", MODELS[model], block, len(x), -2))
    uc.mem_write(syms["emu_in"], struct.pack(f"<{len(x)}f", *x))
    uc.hook_add(UC_HOOK_MEM_WRITE, lambda u, *a: u.emu_stop(), begin=DONE_ADDR, end=DONE_ADDR + 3)
    try:
        uc.emu_start(entry | 1, 0xFFFFFFFF)
    except UcError as e:
        raise SystemExit(f"emulation error: {e} at pc={uc.reg_read(UC_ARM_REG_PC):#x}")
    status = struct.unpack("<i", uc.mem_read(syms["emu_cfg"] + 12, 4))[0]
    if status != 0:
        raise SystemExit(f"harness status {status} (capture not loaded?)")
    return struct.unpack(f"<{len(x)}f", uc.mem_read(syms["emu_out"], 4 * len(x)))


def read_raw(path):
    data = open(path, "rb").read()
    return struct.unpack(f"<{len(data) // 4}f", data)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    x = read_raw(os.path.join(ROOT, "test", "golden_input.raw"))
    fail = False
    for elf_path in sys.argv[1:]:
        segs, syms, entry = load_elf(elf_path)
        print(f"== {os.path.basename(elf_path)}")
        for model in MODELS:
            ref = read_raw(os.path.join(ROOT, "test", f"golden_{model}_output.raw"))
            peak = max(abs(v) for v in ref)
            sig = sum(v * v for v in ref)
            for block in (48, 16, 0):
                t0 = time.time()
                y = run(segs, syms, entry, model, block, x)
                err = [a - b for a, b in zip(y, ref)]
                maxe = max(abs(e) for e in err)
                esr = 10 * __import__("math").log10(sum(e * e for e in err) / sig + 1e-300)
                ok = maxe <= 1e-4 * peak and maxe == maxe
                fail |= not ok
                label = f"block {block}" if block else "varying blocks"
                print(f"  {model} {label:<15} max abs err {maxe:.2e}  ESR {esr:7.1f} dB  "
                      f"{'ok' if ok else 'FAIL'}  ({time.time() - t0:.0f} s)", flush=True)
    print(f"m7emu: Cortex-M7 code vs NeuralAmpModelerCore reference: {'FAIL' if fail else 'PASS'}")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
