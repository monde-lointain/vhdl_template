# SPDX-License-Identifier: MIT
###################################################################
#
# Xilinx Vivado FPGA Makefile
#
# Copyright (c) 2016-2025 Alex Forencich
#
###################################################################
#
# Parameters:
# FPGA_TOP - Top module name
# FPGA_FAMILY - FPGA family (e.g. VirtexUltrascale)
# FPGA_DEVICE - FPGA device (e.g. xcvu095-ffva2104-2-e)
# SYN_FILES - list of source files
# INC_FILES - list of include files
# XDC_FILES - list of timing constraint files
#
# Note: both SYN_FILES and INC_FILES support file list files.  File list
# files are files with a .f extension that contain a list of additional
# files to include, one path relative to the .f file location per line.
# The .f files are processed recursively, and then the complete file list
# is de-duplicated, with later files in the list taking precedence.
#
# Example:
#
# FPGA_TOP = fpga
# FPGA_FAMILY = VirtexUltrascale
# FPGA_DEVICE = xcvu095-ffva2104-2-e
# SYN_FILES = rtl/fpga.v
# XDC_FILES = fpga.xdc
# include ../common/vivado.mk
#
###################################################################

# phony targets
.PHONY: fpga vivado elaborate tmpclean clean distclean

# prevent make from deleting intermediate files and reports
.PRECIOUS: %.xpr %.bit %.bin %.ltx %.xsa %.mcs %.prm
.SECONDARY:

FPGA_TOP ?= fpga
PROJECT ?= $(FPGA_TOP)
XDC_FILES ?= 

# handle file list files
process_f_file = $(call process_f_files,$(addprefix $(dir $1),$(shell cat $1)))
process_f_files = $(foreach f,$1,$(if $(filter %.f,$f),$(call process_f_file,$f),$f))
uniq_base = $(if $1,$(call uniq_base,$(foreach f,$1,$(if $(filter-out $(notdir $(lastword $1)),$(notdir $f)),$f,))) $(lastword $1))
SYN_FILES := $(call uniq_base,$(call process_f_files,$(SYN_FILES)))
INC_FILES := $(call uniq_base,$(call process_f_files,$(INC_FILES)))

###################################################################
# Main Targets
#
# all: create and open Vivado project 
# vivado: open project in Vivado
# tmpclean: remove intermediate files
# clean: remove output files and project files
# distclean: remove archived output files
###################################################################

all: vivado

# elaboration
elaborate: create_project.tcl $(SYN_FILES) $(INC_FILES) | $(PROJECT).xpr
	echo "open_project $(PROJECT).xpr" > elaborate.tcl
	echo "synth_design -rtl -name rtl_1 -flatten_hierarchy full" >> elaborate.tcl
	echo "start_gui" >> elaborate.tcl
	vivado -nojournal -nolog -mode batch -source elaborate.tcl

vivado: $(PROJECT).xpr
	vivado $(PROJECT).xpr

tmpclean::
	-rm -rf *.log *.jou *.cache *.gen *.hbs *.hw *.ip_user_files *.runs *.xpr *.html *.xml *.sim *.srcs *.str .Xil defines.v
	-rm -rf create_project.tcl elaborate.tcl run_synth.tcl run_impl.tcl generate_bit.tcl

clean:: tmpclean
	-rm -rf *.bit *.bin *.ltx *.xsa program.tcl generate_mcs.tcl *.mcs *.prm flash.tcl
	-rm -rf *_utilization.rpt *_utilization_hierarchical.rpt

distclean:: clean
	-rm -rf rev

###################################################################
# Target implementations
###################################################################

# Vivado project file

# create fresh project if Makefile has changed
create_project.tcl: Makefile 
	echo "create_project -force -part $(FPGA_PART) $(PROJECT)" > $@
	echo "add_files -fileset sources_1 $(SYN_FILES)" >> $@
	echo "set_property top $(FPGA_TOP) [current_fileset]" >> $@
	for x in $(CONFIG_TCL_FILES); do echo "source $$x" >> $@; done


$(PROJECT).xpr: create_project.tcl 
	vivado -nojournal -nolog -mode batch $(foreach x,$?,-source $x)
