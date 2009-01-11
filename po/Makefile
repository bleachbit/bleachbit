APP = bleachbit
POFILES = $(wildcard *.po)
MOFILES = $(patsubst %.po,%.mo,$(POFILES))
SRC = $(wildcard ../bleachbit/*.py)
POTFILE = $(APP).pot


$(POTFILE): $(SRC)
	xgettext -o $(APP).pot --default-domain=$(APP) $(SRC)

refresh-po: $(POTFILE)
	for oldpo in $(POFILES); do \
		lang=`basename $$oldpo .po`; \
		msgmerge -v $${lang}.po $(POTFILE) > $${lang}.pot; \
		mv $$lang.pot $$lang.po; \
	done

spelling: $(POTFILE)
	grep msgid $(POTFILE) | cut -c 8- | aspell list

%.mo: %.po
	msgfmt --statistics -o $@ $<
	# copy locally for running without installation
	mkdir -p ../locale/$(@:.mo=)/LC_MESSAGES/
	cp -lf $@ ../locale/$(@:.mo=)/LC_MESSAGES/bleachbit.mo

install: $(MOFILES)
	for MO in $(MOFILES); do \
		lang=`basename $$MO .mo`; \
		DST=$(DESTDIR)/usr/share/locale/$$lang/LC_MESSAGES/; \
		mkdir -p $$DST; \
		cp $$MO $$DST/bleachbit.mo; \
done

clean:
	@rm -fv *.mo

all: $(APP).pot $(MOFILES)

