# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

# On some systems if not explicitly given, make uses /bin/sh
SHELL := /bin/bash

.PHONY: clean install tests build

# if not specified, do not check coverage
PYTHON ?= python3
# Convert Windows backslash paths to forward slashes for bash compatibility
PYTHON_FIXED := $(subst \,/,$(PYTHON))
COVERAGE ?= $(PYTHON_FIXED)

build:
	echo Nothing to build

clean:
	@rm -vf {.,bleachbit,tests,windows,bleachbit/markovify}/*{pyc,pyo,~} # files
	@rm -vrf {.,bleachbit,tests,windows,bleachbit/markovify}/__pycache__ # directories
	@rm -vrf build dist # created by py2exe
	@rm -rf BleachBit-Portable # created by windows/setup_py2exe.bat
	@rm -rf BleachBit-*-portable.zip
	@rm -vf MANIFEST # created by setup.py
	make -C po clean
	@rm -vrf locale
	@rm -vrf {*/,./}*.{pylint,pyflakes}.log
	@rm -vrf windows/BleachBit-*-setup*.{exe,zip}
	@rm -vrf htmlcov .coverage # code coverage reports

install:
	@echo "Linux not supported in this version."
	exit 1

lint:
	[ -x "$$(command -v pyflakes3)" ] ||  echo "WARNING: pyflakes3 not found"
	[ -x "$$(command -v pylint)" ] ||  echo "WARNING: pylint not found"
	for f in *py */*py; \
	do \
		echo "$$f"; \
		( [ -x "$$(command -v pyflakes3)" ] && pyflakes3 "$$f" > "$$f".pyflakes.log ); \
		( [ -x "$$(command -v pylint)" ] && pylint "$$f" > "$$f".pylint.log ); \
	done; \
	exit 0

downgrade_desktop:
#	This will downgrade the version of the .desktop file for older Linux distributions.
#	See https://github.com/bleachbit/bleachbit/issues/750
	desktop-file-validate org.bleachbit.BleachBit.desktop || \
	 sed --regexp-extended -i '/^(Keywords|Version)=/d' org.bleachbit.BleachBit.desktop

tests:
	make -C cleaners tests; cleaners_status=$$?; \
	$(COVERAGE) -m unittest discover -p Test*.py -v; py_status=$$?; \
	exit $$(($$cleaners_status + $$py_status))

pretty:
	autopep8 -i {.,bleachbit,tests}/*py
	dos2unix  {.,bleachbit,tests}/*py
	make -C cleaners pretty
	xmllint --format doc/cleaner_markup_language.xsd > doc/cleaner_markup_language.xsd.tmp
	mv doc/cleaner_markup_language.xsd.tmp doc/cleaner_markup_language.xsd
