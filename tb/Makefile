TOPLEVEL_LANG := vhdl

SIM ?= ghdl

COCOTB_HDL_TIMEUNIT=1us
COCOTB_HDL_TIMEPRECISION=1us

RTL_DIR = ../rtl

DUT = tinyalu
TOPLEVEL := $(DUT)
MODULE := test_$(DUT)
VHDL_SOURCES = \
	$(RTL_DIR)/$(DUT).vhd \
	$(RTL_DIR)/single_cycle_add_and_xor.vhd \
	$(RTL_DIR)/three_cycle_mult.vhd \

COCOTB_REDUCED_LOG_FMT = True

include $(shell cocotb-config --makefiles)/Makefile.sim

.PHONY: testclean checkclean check

check:
	./combine_results.py

testclean: clean
	rm -rf __pycache__
	rm -rf results.xml
	rm -rf combined_results.xml
	rm -rf log.txt
	rm -rf sim_build
	rm -rf modelsim.ini
	rm -rf transcript

checkclean: check testclean
