# Cortex-M7 emulation test: build the engines for the Cortex-M7 with their
# assembly kernels, run them under emulation (Unicorn) and compare the output
# with the NeuralAmpModelerCore references.
#
#   make check          # needs arm-none-eabi-gcc with newlib, python3 with
#                       # unicorn and pyelftools (pip install unicorn pyelftools)
#   make check PYTHON=.venv/bin/python ARM_GCC=/path/to/arm-none-eabi-gcc
#
# One image per Cortex-M7 tuning (a2lite/a2full, and -b16 where it exists).

ARM_GCC ?= arm-none-eabi-gcc
PYTHON  ?= python3
ROOT    := ../..
ENG     := $(ROOT)/engines/cortex-m7
TUNES   := $(sort $(patsubst $(ENG)/%,%,$(wildcard $(ENG)/*-b*)))
CFLAGS  := -mcpu=cortex-m7 -mthumb -mfpu=fpv5-sp-d16 -mfloat-abi=hard -O2 -ffast-math \
           -std=c99 -Wall -Wextra -Werror
LDFLAGS := -T link.ld -nostartfiles -specs=nosys.specs -Wl,--gc-sections

# $(1): image name, $(2): A2-Lite engine dir, $(3): A2-Full engine dir
define image
build/$(1).elf: emu_main.c startup.c link.ld $(ROOT)/example/a2_engine.c $(2)/nam_a2lite.c $(3)/nam_a2full.c
	@mkdir -p build
	$(ARM_GCC) $(CFLAGS) -I$(ROOT)/example -I$(2) -I$(3) -I$(ROOT)/namb \
	    '-DEMU_NAMB_A2LITE="$(ROOT)/weights/a2lite.namb"' '-DEMU_NAMB_A2FULL="$(ROOT)/weights/a2full.namb"' \
	    startup.c emu_main.c $(ROOT)/example/a2_engine.c $(2)/nam_a2lite.c $(3)/nam_a2full.c \
	    $(ROOT)/namb/namb_reader.c $(LDFLAGS) -lm -o $$@
endef

engine = $(firstword $(wildcard $(ENG)/$(1)$(2)) $(ENG)/$(1))
IMAGES := emu $(foreach t,$(sort $(patsubst a2lite%,%,$(patsubst a2full%,%,$(TUNES)))),emu$(t))
$(eval $(call image,emu,$(ENG)/a2lite,$(ENG)/a2full))
$(foreach t,$(filter-out emu,$(IMAGES)),$(eval $(call image,$(t),$(call engine,a2lite,$(t:emu%=%)),$(call engine,a2full,$(t:emu%=%)))))

check: $(IMAGES:%=build/%.elf)
	$(PYTHON) m7emu.py $^

clean:
	rm -rf build

.PHONY: check clean
