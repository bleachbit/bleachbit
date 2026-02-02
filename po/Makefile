APP = bleachbit
POFILES = $(wildcard *.po)
MOFILES = $(patsubst %.po,%.mo,$(POFILES))
SRC = $(wildcard ../bleachbit/*.py) ../share/app-menu.ui
POTFILE = $(APP).pot
ITS ?= /usr/share/gettext/its/metainfo.its
PYTHON ?= python3


.PHONY: refresh-po spelling local install clean all require-gettext

require-gettext:
	@missing=0; \
	for c in xgettext msgmerge msgfmt msggrep; do \
		command -v $$c >/dev/null 2>&1 || missing=1; \
	done; \
	if [ $$missing -ne 0 ]; then \
		echo "ERROR: Missing gettext. APT users, try: sudo apt install gettext"; \
		exit 1; \
	fi

cleanerml.pot: ../bleachbit/CleanerML.py ../cleaners/*xml
	$(PYTHON) ../bleachbit.py --pot

desktop.pot: ../org.bleachbit.BleachBit.desktop
	echo "#: ../org.bleachbit.BleachBit.desktop" > desktop.pot
	echo "msgid \"`perl -n -e '/GenericName=(.*)$$/ && print "$$1\n"' ../org.bleachbit.BleachBit.desktop`\"" >> desktop.pot
	echo "msgstr \"\"" >> desktop.pot
	echo >> desktop.pot
	echo "#: ../org.bleachbit.BleachBit.desktop" >> desktop.pot
	echo "msgid \"`perl -n -e '/Comment=(.*)$$/ && print "$$1\n"' ../org.bleachbit.BleachBit.desktop`\"" >> desktop.pot
	echo "msgstr \"\"" >> desktop.pot
	echo >> desktop.pot

metainfo.pot: ../org.bleachbit.BleachBit.metainfo.xml require-gettext
	@echo "* Extracting translatable strings from metainfo.xml using xgettext with ITS"
	@if [ -f "$(ITS)" ]; then \
		xgettext -o $@ \
			--from-code=UTF-8 \
			--add-comments=TRANSLATORS \
			--add-location=file \
			--its=$(ITS) \
			$<; \
	else \
		echo "WARNING: Required file '$(ITS)' is missing. Skipping metainfo extraction (creating stub)."; \
		echo "APT users, try: sudo apt install appstream"; \
		echo '# metainfo.pot stub (ITS file missing)' > $@; \
	fi

nsis.pot: ../windows/NsisInclude/NsisMultiUserLang.nsh ../windows/nsis_translations.py
	$(PYTHON) ../windows/nsis_translations.py --pot

$(POTFILE): $(SRC) cleanerml.pot desktop.pot metainfo.pot nsis.pot require-gettext
	@echo "* Generating $(POTFILE)"
	@if [ -f $(POTFILE) ]; then \
		cp $(POTFILE) $(POTFILE).old; \
		echo " Words before update: "; \
		tail -n +20 $(POTFILE) | grep -v ^# | sed "s/\(msgstr\|msgid\)//g" | sort | uniq |wc --words; \
	fi
	cat cleanerml.pot desktop.pot metainfo.pot nsis.pot > $(POTFILE)
	# --add-location=file: reduces size of diff
	xgettext -o $(POTFILE) \
		--join-existing \
		--add-comments=TRANSLATORS \
		--keyword="_p:1c,2" \
		--default-domain=$(APP) \
		--add-location=file \
		$(SRC)
	sed -i 's/charset=CHARSET/charset=utf-8/g' $(POTFILE)
	echo " Words after update: " \
		`tail -n +20 $(POTFILE) | grep -v ^# | sed "s/\(msgstr\|msgid\)//g" | sort | uniq | wc --words`
	if [ -f $(POTFILE).old ]; then \
		echo "msgid added or removed"; \
		msgcomm -u $(POTFILE) $(POTFILE).old > diff.pot; \
		sed -e '1,/^"Plural-Forms:/d' -e '/^#/d' -e '/^msgstr/d' -e '/^$$/d' diff.pot; \
	fi


refresh-po: $(POTFILE) require-gettext
	@echo "* Refreshing .po files"
	for oldpo in $(POFILES); do \
		lang=`basename $$oldpo .po`; \
		echo $$lang; \
		msgmerge --no-fuzzy-matching -v $${lang}.po $(POTFILE) > $${lang}.pot; \
		mv $$lang.pot $$lang.po; \
	done

spelling: $(POTFILE) require-gettext
	@echo "* Checking spelling"
	@echo
	@echo Word count: `msggrep -Kie . --no-wrap $(POTFILE)  | grep ^msgid  | cut -c 8- | wc --words`
	@echo
	@command -v aspell >/dev/null 2>&1 || { echo "WARNING: Missing 'aspell'. apt users, try: sudo apt install aspell"; exit 0; }
	msggrep -Kie . --no-wrap $(POTFILE)  | grep ^msgid  | cut -c 8- | aspell --personal=./aspell.pws list | sort -u

%.mo: %.po require-gettext
	@echo "* Generating $@"
	msgfmt --statistics -o $@ $<

local: $(MOFILES)
	@echo "* Copy locally for running without system installation"
	for mofile in $(MOFILES); do \
		lang=`basename $$mofile .mo`; \
		mkdir -p ../locale/$$lang/LC_MESSAGES/; \
		cp -lf $$mofile ../locale/$$lang/LC_MESSAGES/bleachbit.mo; \
	done
	@echo "To launch the application, run this in the project root directory:"
	@echo "$(PYTHON) bleachbit.py"

install: $(MOFILES)
	echo "* Installing in $(DESTDIR)/usr/share/locale"
	for MO in $(MOFILES); do \
		lang=`basename $$MO .mo`; \
		DST=$(DESTDIR)/usr/share/locale/$$lang/LC_MESSAGES/; \
		mkdir -p $$DST; \
		cp $$MO $$DST/bleachbit.mo; \
	done

clean:
	echo "* Cleaning"
	@rm -fv -- *.mo
	# Keep $(POTFILE) because it is stored in Git for Weblate.
	@rm -fv $(POTFILE).old cleanerml.pot desktop.pot metainfo.pot nsis.pot diff.pot
	@rm -rfv ../locale

all: $(POTFILE) $(MOFILES)
