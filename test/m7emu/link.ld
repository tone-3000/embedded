ENTRY(_start)
MEMORY { RAM (rwx) : ORIGIN = 0x20000000, LENGTH = 32M }
SECTIONS {
  .text : { KEEP(*(.vectors)) *(.text*) *(.rodata*) KEEP(*(.init)) KEEP(*(.fini)) } > RAM
  .ARM.extab : { *(.ARM.extab* .gnu.linkonce.armextab.*) } > RAM
  .ARM.exidx : { __exidx_start = .; *(.ARM.exidx*) __exidx_end = .; } > RAM
  .preinit_array : { PROVIDE_HIDDEN(__preinit_array_start = .); KEEP(*(.preinit_array*)) PROVIDE_HIDDEN(__preinit_array_end = .); } > RAM
  .init_array : { PROVIDE_HIDDEN(__init_array_start = .); KEEP(*(SORT(.init_array.*))) KEEP(*(.init_array*)) PROVIDE_HIDDEN(__init_array_end = .); } > RAM
  .fini_array : { PROVIDE_HIDDEN(__fini_array_start = .); KEEP(*(.fini_array*)) PROVIDE_HIDDEN(__fini_array_end = .); } > RAM
  .data : { *(.data*) } > RAM
  .bss (NOLOAD) : { __bss_start__ = .; *(.bss*) *(COMMON) *(.dtcmram_bss) __bss_end__ = .; } > RAM
  . = ALIGN(8); end = .; _end = .; PROVIDE(__end__ = .);
  __stack_top = ORIGIN(RAM) + LENGTH(RAM);
}
