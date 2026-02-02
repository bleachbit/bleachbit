# Copyright (C) 2008-2025 Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: You are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
# Makefile edited by https://github.com/Tobias-B-Besemer
# Done on 2019-03-13

# On some systems if not explicitly given, make uses /bin/sh
SHELL := /bin/bash

.PHONY: clean install tests build tests-with-sudo lint delete_windows_files pretty

prefix ?= /usr/local
bindir ?= $(prefix)/bin
datadir ?= $(prefix)/share

INSTALL = install
INSTALL_DATA = $(INSTALL) -m 644
INSTALL_SCRIPT = $(INSTALL) -m 755

# if not specified, do not check coverage
PYTHON ?= python3
COVERAGE ?= $(PYTHON)

ifneq ($(COVERAGE),$(PYTHON))
BLEACHBIT_SUDO_COVERAGE_RUNNER := $(COVERAGE) --append
BLEACHBIT_SUDO_COVERAGE_FILE := $(if $(COVERAGE_FILE),$(COVERAGE_FILE),.coverage)
else
BLEACHBIT_SUDO_COVERAGE_RUNNER :=
BLEACHBIT_SUDO_COVERAGE_FILE :=
endif

build:
	echo Nothing to build

clean:
	@rm -vf {.,bleachbit,tests,windows,bleachbit/markovify}/*{pyc,pyo,~} # files
	@rm -vrf {.,bleachbit,tests,windows,bleachbit/markovify}/__pycache__ # directories
	@rm -vrf build dist # created by py2exe
	@rm -rf BleachBit-Portable # created by windows/setup.bat
	@rm -rf BleachBit-*-portable.zip
	@rm -vf MANIFEST # created by setup.py
	$(MAKE) -C po clean
	@rm -vrf locale
	@rm -vrf {*/,./}*.{pylint,pyflakes}.log
	@rm -vrf windows/BleachBit-*-setup*.{exe,zip}
	@rm -vrf htmlcov .coverage # code coverage reports
	@rm -vrf *.egg-info # Python package metadata
	@rm -vrf docker-artifacts # Docker build outputs

install:
	# "binary"
	mkdir -p $(DESTDIR)$(bindir)
	$(INSTALL_SCRIPT) bleachbit.py $(DESTDIR)$(bindir)/bleachbit

	# application launcher
	mkdir -p $(DESTDIR)$(datadir)/applications
	$(INSTALL_DATA) org.bleachbit.BleachBit.desktop $(DESTDIR)$(datadir)/applications/

	# AppStream metadata
	mkdir -p $(DESTDIR)$(datadir)/metainfo
	$(INSTALL_DATA) org.bleachbit.BleachBit.metainfo.xml $(DESTDIR)$(datadir)/metainfo/

	# Python code
	mkdir -p $(DESTDIR)$(datadir)/bleachbit/markovify
	$(INSTALL_DATA) bleachbit/*.py $(DESTDIR)$(datadir)/bleachbit
	$(INSTALL_DATA) bleachbit/markovify/*.py $(DESTDIR)$(datadir)/bleachbit/markovify
	#note: compileall is recursive
	cd $(DESTDIR)$(datadir)/bleachbit && \
	$(PYTHON) -O -c "import compileall; compileall.compile_dir('.')" && \
	$(PYTHON) -c "import compileall; compileall.compile_dir('.')"

	# cleaners
	mkdir -p $(DESTDIR)$(datadir)/bleachbit/cleaners
	$(INSTALL_DATA) cleaners/*.xml $(DESTDIR)$(datadir)/bleachbit/cleaners

	# share files
	mkdir -p $(DESTDIR)$(datadir)/bleachbit/share
	$(INSTALL_DATA) share/app-menu.ui $(DESTDIR)$(datadir)/bleachbit/share
	$(INSTALL_DATA) share/protected_path.xml $(DESTDIR)$(datadir)/bleachbit/share

	# icon
	mkdir -p $(DESTDIR)$(datadir)/pixmaps
	$(INSTALL_DATA) bleachbit.png $(DESTDIR)$(datadir)/pixmaps/

	# translations
	$(MAKE) -C po install DESTDIR=$(DESTDIR)

	# PolicyKit
	mkdir -p $(DESTDIR)$(datadir)/polkit-1/actions
	$(INSTALL_DATA) org.bleachbit.policy $(DESTDIR)$(datadir)/polkit-1/actions/

lint:
	command -v pyflakes3 >/dev/null 2>&1 || echo "WARNING: Missing pyflakes3. APT users, try: sudo apt install pyflakes3"
	command -v pylint >/dev/null 2>&1 || echo "WARNING: Missing pylint. APT users, try: sudo apt install pylint"
	for f in *py */*py; \
	do \
		echo "$$f"; \
		( pyflakes3 "$$f" > "$$f".pyflakes.log ); \
		( pylint "$$f" > "$$f".pylint.log ); \
	done; \
	exit 0

delete_windows_files:
	# This is used for building .deb and .rpm packages.
	# Remove Windows-specific cleaners.
	grep -l "cleaner id=\"\w*\" os=\"windows\"" cleaners/*xml | xargs rm -f
	# Remove Windows-specific code.
	rm -f bleachbit/{Winapp,Windows*}.py tests/TestWindows{,Wipe}.py
	# Remove the whole directory after verifying it's the Windows build directory.
	@if [ -f windows/bleachbit.nsi ]; then \
		rm -rf windows; \
	else \
		echo "WARNING: windows/bleachbit.nsi not found, skipping windows directory removal"; \
	fi

tests:
	# Catch warnings as errors. Also set in `tests/common.py`.
	$(MAKE) -C cleaners tests; cleaners_status=$$?; \
	PYTHONWARNINGS=error $(COVERAGE) -m unittest discover -p Test*.py -v; py_status=$$?; \
	exit $$(($$cleaners_status + $$py_status))

tests-with-sudo:
	# Run tests marked with @test_also_with_sudo using sudo
	PYTHONWARNINGS=error \
		BLEACHBIT_COVERAGE_RUNNER="$(BLEACHBIT_SUDO_COVERAGE_RUNNER)" \
		BLEACHBIT_COVERAGE_FILE="$(BLEACHBIT_SUDO_COVERAGE_FILE)" \
		$(PYTHON) tests/test_with_sudo.py

pretty:
	@if command -v autopep8 >/dev/null 2>&1; then \
		autopep8 -i {.,bleachbit,tests}/*py; \
	else \
		echo "WARNING: Missing autopep8. APT users, try: sudo apt install python3-autopep8"; \
	fi
	@if command -v dos2unix >/dev/null 2>&1; then \
		dos2unix {.,bleachbit,tests}/*py; \
	else \
		echo "WARNING: Missing dos2unix. APT users, try: sudo apt install dos2unix"; \
	fi
	$(MAKE) -C cleaners pretty
	if command -v xmllint >/dev/null 2>&1; then \
		xmllint --format doc/cleaner_markup_language.xsd > doc/cleaner_markup_language.xsd.tmp; \
		mv doc/cleaner_markup_language.xsd.tmp doc/cleaner_markup_language.xsd; \
	else \
		echo "WARNING: Missing xmllint. APT users, try: sudo apt install libxml2-utils"; \
	fi
