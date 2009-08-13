.PHONY: clean install tests build

prefix ?= /usr/local
bindir ?= $(prefix)/bin
datadir ?= $(prefix)/share

INSTALL = install
INSTALL_DATA = $(INSTALL) -m 644


build:
	echo Nothing to build

clean:
	@rm -vf {.,bleachbit}/*{pyc,pyo,~}
	@rm -vf dist/bleachbit-*.tar.bz2
	@rm -vf MANIFEST
	make -C po clean
	@rm -vrf locale
	@rm -vfr {*/,./}*.{pychecker,pylint,pyflakes}.log

install:
	# "binary"
	mkdir -p $(DESTDIR)$(bindir)
	ln -f -s ../..$(datadir)/bleachbit/GUI.py $(DESTDIR)$(bindir)/bleachbit

	# .desktop
	mkdir -p $(DESTDIR)$(datadir)/applications
	$(INSTALL_DATA) bleachbit.desktop $(DESTDIR)$(datadir)/applications/

	# Python code
	mkdir -p $(DESTDIR)$(datadir)/bleachbit
	$(INSTALL_DATA) bleachbit/*.py $(DESTDIR)$(datadir)/bleachbit
	chmod 0755 $(DESTDIR)$(datadir)/bleachbit/GUI.py
	cd $(DESTDIR)$(datadir)/bleachbit && \
	python -O -c "import compileall; compileall.compile_dir('.')" && \
	python -c "import compileall; compileall.compile_dir('.')"

	# cleaners
	mkdir -p $(DESTDIR)$(datadir)/bleachbit/cleaners
	$(INSTALL_DATA) cleaners/*xml $(DESTDIR)$(datadir)/bleachbit/cleaners

	# icon
	mkdir -p $(DESTDIR)$(datadir)/pixmaps
	$(INSTALL_DATA) bleachbit.png $(DESTDIR)$(datadir)/pixmaps/

	# translations
	make -C po install DESTDIR=$(DESTDIR)

lint:
	for f in *py */*py; \
	do \
		echo "$$f" ; \
		pychecker "$$f" > "$$f".pychecker.log ; \
		pyflakes "$$f" > "$$f".pyflakes.log ; \
		pylint "$$f" > "$$f".pylint.log ; \
	done; \
	exit 0

tests:
	make -C cleaners tests
	cd bleachbit && \
	for f in `grep -l unittest *py`; \
	do \
		echo testing "$$f"; \
		python "$$f" -v; \
		rc=$$?; \
		[ $$rc -gt 0 ] && echo -e \\a && notify-send -u critical "error executing test for $$f" && exit 1; \
	done; \
	exit 0


