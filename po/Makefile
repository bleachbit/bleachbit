APP = bleachbit
POFILES = $(wildcard *.po)
MOFILES = $(patsubst %.po,%.mo,$(POFILES))
SRC = $(wildcard ../bleachbit/*.py) ../data/app-menu.ui
POTFILE = $(APP).pot
ITS = /usr/share/gettext/its/metainfo.its

# Use PYTHON environment variable if available, otherwise default to python3
PYTHON ?= python3


.PHONY: refresh-po spelling local install clean all

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

metainfo.pot: ../org.bleachbit.BleachBit.metainfo.xml
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

$(POTFILE): $(SRC) cleanerml.pot desktop.pot metainfo.pot
	@echo "* Generating $(POTFILE)"
	@if [ -f $(POTFILE) ]; then \
		cp $(POTFILE) $(POTFILE).old; \
		echo " Words before update: "; \
		tail -n +20 $(POTFILE) | grep -v ^# | sed "s/\(msgstr\|msgid\)//g" | sort | uniq |wc --words; \
	fi
	cat cleanerml.pot desktop.pot metainfo.pot > $(POTFILE)
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


refresh-po: $(POTFILE)
	@echo "* Refreshing .po files"
	for oldpo in $(POFILES); do \
		lang=`basename $$oldpo .po`; \
		echo $$lang; \
		msgmerge --no-fuzzy-matching -v $${lang}.po $(POTFILE) > $${lang}.pot; \
		mv $$lang.pot $$lang.po; \
	done

spelling: $(POTFILE)
	@echo "* Checking spelling"
	@echo
	@echo Word count: `msggrep -Kie . --no-wrap $(POTFILE)  | grep ^msgid  | cut -c 8- | wc --words`
	@echo
	msggrep -Kie . --no-wrap $(POTFILE)  | grep ^msgid  | cut -c 8- | aspell --personal=./aspell.pws list | sort -u

%.mo: %.po
	@echo "* Generating $@"
	msgfmt --statistics -o $@ $<

local: $(MOFILES)
	@echo "* Copy locally for running without system installation"
	for mofile in $(MOFILES); do \
		lang=`basename $$mofile .mo`; \
		mkdir -p ../locale/$$lang/LC_MESSAGES/; \
		cp -lf $$mofile ../locale/$$lang/LC_MESSAGES/bleachbit.mo; \
	done
	@echo "Now you can run cd ..; $(PYTHON) bleachbit/GUI.py"

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
	@rm -fv *.mo
	@rm -fv $(POTFILE) $(POTFILE).old cleanerml.pot desktop.pot metainfo.pot diff.pot
	@rm -rfv ../locale

all: $(POTFILE) $(MOFILES)
