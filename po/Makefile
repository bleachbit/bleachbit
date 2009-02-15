APP = bleachbit
POFILES = $(wildcard *.po)
MOFILES = $(patsubst %.po,%.mo,$(POFILES))
SRC = $(wildcard ../bleachbit/*.py)
POTFILE = $(APP).pot


.PHONY: refresh-po spelling local install clean all

cleanerml.pot: ../bleachbit/CleanerML.py ../cleaners/*xml
	python ../bleachbit/CleanerML.py pot

$(POTFILE): $(SRC) cleanerml.pot
	@echo "* Generating $(APP).pot"
	cp cleanerml.pot $(APP).pot
	xgettext -o $(APP).pot --join-existing --default-domain=$(APP) $(SRC)

refresh-po: $(POTFILE)
	@echo "* Refreshing .po files"
	for oldpo in $(POFILES); do \
		lang=`basename $$oldpo .po`; \
		msgmerge -v $${lang}.po $(POTFILE) > $${lang}.pot; \
		mv $$lang.pot $$lang.po; \
	done

spelling: $(POTFILE)
	@echo "* Checking spelling"
	@echo
	@echo "** English"
	grep msgid $(POTFILE) | cut -c 8- | aspell list
	@echo 
	@echo "** Spanish"
	grep msgstr es.po | cut -c 8- | LANG=es_ES.utf8 aspell list

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
	@echo "Now you can run cd ..; python bleachbit/GUI.py"

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
	@rm -fv $(APP).pot cleanerml.pot
	@rm -rfv ../locale

all: $(APP).pot $(MOFILES)

