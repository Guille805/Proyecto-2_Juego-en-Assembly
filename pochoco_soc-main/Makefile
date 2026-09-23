# Copyright 2026 Universidad de los Andes.
# Licensed under the Solderpad Hardware License, Version 0.51 (the "License");
# you may not use this file except in compliance with the License.
# SPDX-License-Identifier: SHL-0.51
#
# Course: Arquitectura de Computadores (2026)
# 
# Authors:
# - Nicolás Villegas <navillegas@miuandes.cl>

# Configuration
TOP  := game_top
PCF  := goboard.pcf

# RTL Sources
SRC  := $(wildcard ./rtl/*.v ./rtl/**/*.v)

# Build Targets
JSON := $(TOP).json
ASC  := $(TOP).asc
BIN  := $(TOP).bin

.PHONY: all prog clean test

# Default target
all: $(BIN)

PYTHON ?= python

sw/game.hex: sw/game.s sw/assembler.py
	$(PYTHON) sw/assembler.py sw/game.s -o $@

# Step 1: Synthesis using Yosys
$(JSON): $(SRC) sw/game.hex Makefile
	yosys -p "read_verilog $(SRC); synth_ice40 -noabc -top $(TOP) -json ${TOP}.json; stat"

# Step 2: Place and Route using NextPNR
$(ASC): $(JSON) $(PCF) Makefile
	nextpnr-ice40 --freq 25 --hx1k --package vq100 --json $(JSON) --pcf $(PCF) --asc $(ASC)

# Step 3: Bitstream Generation
$(BIN): $(ASC)
	icepack $(ASC) $(BIN)

# Step 4: Flash the Board
prog: $(BIN)
	iceprog $(BIN)

# Clean up generated files
clean:
	rm -f $(JSON) $(ASC) $(BIN)

# Regression tests (Python + Icarus Verilog)
test:
	$(PYTHON) -B tests/run_tests.py
