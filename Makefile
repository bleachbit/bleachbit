# Copyright (C) 2008-2020 Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: You are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
# Makefile edited by https://github.com/Tobias-B-Besemer
# Done on 2019-03-13

# On some systems if not explicitly given, make uses /bin/sh
SHELL := /bin/bash

.PHONY: clean install tests build

prefix ?= /usr/local
bindir ?= $(prefix)/bin
datadir ?= $(prefix)/share

INSTALL = install
INSTALL_DATA = $(INSTALL) -m 644

# if not specified, do not check coverage
PYTHON ?= python3
COVERAGE ?= $(PYTHON)

build:
	echo Nothing to build

clean:
	@rm -vf {.,bleachbit,tests,windows}/*{pyc,pyo,~}
	@rm -vrf build dist # created by py2exe
	@rm -rf BleachBit-Portable # created by windows/setup_py2exe.bat
	@rm -rf BleachBit-*-portable.zip
	@rm -vf MANIFEST # created by setup.py
	make -C po clean
	@rm -vrf locale
	@rm -vrf {*/,./}*.{pychecker,pylint,pyflakes}.log
	@rm -vrf windows/BleachBit-*-setup*.{exe,zip}
	@rm -vrf htmlcov .coverage # code coverage reports

install:
	# "binary"
	mkdir -p $(DESTDIR)$(bindir)
	$(INSTALL_DATA) bleachbit.py $(DESTDIR)$(bindir)/bleachbit
	chmod 0755 $(DESTDIR)$(bindir)/bleachbit

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

	# menu
	$(INSTALL_DATA) data/app-menu.ui $(DESTDIR)$(datadir)/bleachbit

	# icon
	mkdir -p $(DESTDIR)$(datadir)/pixmaps
	$(INSTALL_DATA) bleachbit.png $(DESTDIR)$(datadir)/pixmaps/

	# translations
	make -C po install DESTDIR=$(DESTDIR)

	# PolicyKit
	mkdir -p $(DESTDIR)$(datadir)/polkit-1/actions
	$(INSTALL_DATA) org.bleachbit.policy $(DESTDIR)$(datadir)/polkit-1/actions/

lint:
	[ -x "$$(command -v pychecker)" ] ||  echo "WARNING: pychecker not found"
	[ -x "$$(command -v pyflakes)" ] ||  echo "WARNING: pyflakes not found"
	[ -x "$$(command -v pylint)" ] ||  echo "WARNING: pylint not found"
	for f in *py */*py; \
	do \
		echo "$$f"; \
		( [ -x "$$(command -v pychecker)" ] && pyflakes "$$f" > "$$f".pychecker.log ); \
		( [ -x "$$(command -v pyflakes)" ] && pyflakes "$$f" > "$$f".pyflakes.log ); \
		( [ -x "$$(command -v pylint)" ] && pylint "$$f" > "$$f".pylint.log ); \
	done; \
	exit 0

delete_windows_files:
	# This is used for building .deb and .rpm packages.
	# Remove Windows-specific cleaners.
	awk '/os=\"windows/ && /id=\"/ {print FILENAME}' cleaners/*.xml | xargs rm -f
	# Remove Windows-specific modules.
	rm -f bleachbit/Windows*.py

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
