APP = bleachbit
POFILES = $(wildcard *.po)
MOFILES = $(patsubst %.po,%.mo,$(POFILES))
SRC = $(wildcard ../bleachbit/*.py)
POTFILE = $(APP).pot


.PHONY: refresh-po spelling local install clean all

cleanerml.pot: ../bleachbit/CleanerML.py ../cleaners/*xml
	python ../bleachbit.py --pot

desktop.pot: ../bleachbit.desktop
	echo "#: ../bleachbit.desktop" > desktop.pot
	echo "msgid \"`perl -n -e '/GenericName=(.*)$$/ && print "$$1\n"' ../bleachbit.desktop`\"" >> desktop.pot
	echo "msgstr \"\"" >> desktop.pot
	echo >> desktop.pot
	echo "#: ../bleachbit.desktop" >> desktop.pot
	echo "msgid \"`perl -n -e '/Comment=(.*)$$/ && print "$$1\n"' ../bleachbit.desktop`\"" >> desktop.pot
	echo "msgstr \"\"" >> desktop.pot
	echo >> desktop.pot


$(POTFILE): $(SRC) cleanerml.pot desktop.pot
	@echo "* Generating $(APP).pot"
	echo " Words before update: " \
		`tail -n +20 bleachbit.pot | grep -v ^# | sed "s/\(msgstr\|msgid\)//g" | sort | wc --words`
	cat cleanerml.pot desktop.pot > $(APP).pot
	xgettext -o $(APP).pot \
		--join-existing \
		--add-comments=TRANSLATORS \
		--keyword="_p:1c,2" \
		--default-domain=$(APP) \
		$(SRC)
	sed -i 's/charset=CHARSET/charset=utf-8/g' bleachbit.pot
	echo " Words after update: " \
		`tail -n +20 bleachbit.pot | grep -v ^# | sed "s/\(msgstr\|msgid\)//g" | sort | wc --words`


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
	msggrep -Kie . --no-wrap $(POTFILE)  | grep ^msgid  | cut -c 8- | aspell  list | sort -u

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
	@rm -fv $(APP).pot cleanerml.pot desktop.pot
	@rm -rfv ../locale

all: $(APP).pot $(MOFILES)

