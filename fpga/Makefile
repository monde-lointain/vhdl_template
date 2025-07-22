# SPDX-License-Identifier: MIT
#
# Copyright (c) 2025 FPGA Ninja, LLC
#
# Authors:
# - Alex Forencich
#

# FPGA settings
FPGA_PART = xc7a35tcpg236-1 
FPGA_TOP = tinyalu
FPGA_ARCH = artix7

RTL_DIR = ../rtl
LIB_DIR = ../lib

# Files for synthesis
SYN_FILES = \
	$(RTL_DIR)/tinyalu.vhd \
	$(RTL_DIR)/three_cycle_mult.vhd \
	$(RTL_DIR)/single_cycle_add_and_xor.vhd

# XDC files
XDC_FILES = 

include ../common/vivado.mk
