APP = bleachbit
POFILES = $(wildcard *.po)
MOFILES = $(patsubst %.po,%.mo,$(POFILES))
PYSRC = $(wildcard ../bleachbit/*.py)
UISRC = ../data/app-menu.ui
POTFILE = $(APP).pot

# Use PYTHON environment variable if available, otherwise default to python3
PYTHON ?= python3
# Convert Windows backslash paths to forward slashes for bash compatibility
PYTHON_FIXED := $(subst \,/,$(PYTHON))

# Download GNOME gtkbuilder ITS rules on demand (MSYS2 gettext lacks them)
ITS_URL = https://raw.githubusercontent.com/GNOME/gtk/gtk-3-24/gtk

.PHONY: refresh-po spelling local install clean all

its/gtkbuilder.its:
	mkdir -p its
	curl -fsSL -o $@ $(ITS_URL)/gtkbuilder.its

its/gtkbuilder.loc:
	mkdir -p its
	curl -fsSL -o $@ $(ITS_URL)/gtkbuilder.loc

cleanerml.pot: ../bleachbit/CleanerML.py ../cleaners/*xml
	$(PYTHON_FIXED) ../bleachbit.py --pot
	$(PYTHON_FIXED) normalize_po.py cleanerml.pot

ui.pot: $(UISRC) its/gtkbuilder.its its/gtkbuilder.loc
	@rm -f ui.pot.ok
	@if xgettext -o ui.pot \
		--add-comments=TRANSLATORS \
		--add-location=file \
		--keyword="_p:1c,2" \
		--default-domain=$(APP) \
		--from-code=UTF-8 \
		--its=its/gtkbuilder.its \
		$(UISRC); then \
		touch ui.pot.ok; \
	else \
		echo "* Warning: xgettext failed for $(UISRC); skipping ui.pot"; \
		touch ui.pot; \
	fi

$(POTFILE): $(PYSRC) cleanerml.pot ui.pot
	@echo "* Generating $(APP).pot"
	echo " Words before update: " \
		`tail -n +20 bleachbit.pot | grep -v ^# | sed "s/\(msgstr\|msgid\)//g" | sort | wc --words`
	cat cleanerml.pot > $(APP).pot
	xgettext -o $(APP).pot \
		--join-existing \
		--add-comments=TRANSLATORS \
		--add-location=file \
		--keyword="_p:1c,2" \
		--default-domain=$(APP) \
		--from-code=UTF-8 \
		$(PYSRC)
	@if [ -f ui.pot.ok ]; then \
		msgcat -o $(APP).pot $(APP).pot ui.pot; \
		rm -f ui.pot.ok; \
	fi
	sed -i 's/charset=CHARSET/charset=utf-8/g' bleachbit.pot
	# Normalize line endings and path separators in comments.
	# This Python script was more reliable here on Windows than sed.
	$(PYTHON_FIXED) normalize_po.py $(POTFILE)
	echo " Words after update: " \
		`tail -n +20 bleachbit.pot | grep -v ^# | sed "s/\(msgstr\|msgid\)//g" | sort | wc --words`


refresh-po: $(POTFILE)
	@echo "* Refreshing .po files"
	$(PYTHON_FIXED) normalize_po.py $(POTFILE)
	for oldpo in $(POFILES); do \
		lang=`basename $$oldpo .po`; \
		echo $$lang; \
		msgmerge --no-fuzzy-matching -v $${lang}.po $(POTFILE) > $${lang}.pot; \
		$(PYTHON_FIXED) normalize_po.py $${lang}.pot; \
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
	@echo "Now you can run cd ..; $(PYTHON_FIXED) bleachbit/GUI.py"

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
	@rm -fv $(APP).pot cleanerml.pot ui.pot ui.pot.ok
	@rm -rfv ../locale
	@rm -rfv its

all: $(APP).pot $(MOFILES)

