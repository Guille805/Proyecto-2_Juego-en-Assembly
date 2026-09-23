PYTHON ?= python
SRCS := $(wildcard *.s)
HEXS := $(SRCS:.s=.hex)
PROGS := $(basename $(SRCS))
all: $(HEXS)
$(PROGS): %: %.hex
%.hex: %.s assembler.py
	$(PYTHON) assembler.py $< -o $@
.PHONY: all $(PROGS)
