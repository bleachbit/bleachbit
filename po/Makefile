APP = bleachbit
POFILES = $(wildcard *.po)
MOFILES = $(patsubst %.po,%.mo,$(POFILES))
SRC = $(wildcard ../bleachbit/*.py)
POTFILE = $(APP).pot


$(POTFILE): $(SRC)
	xgettext -o $(APP).pot --default-domain=$(APP) $(SRC)

refresh-po: $(POTFILE)
	for oldpo in $(POFILES); do \
		lang=$${oldpo%.*}; \
		msgmerge -v $${lang}.po $(POTFILE) > $${lang}.pot; \
		mv $$lang.pot $$lang.po; \
	done

%.mo: %.po
	msgfmt --statistics -o $@ $<
	# copy locally for running without installation
	mkdir -p ../locale/$(@:.mo=)/LC_MESSAGES/
	cp -lf $@ ../locale/$(@:.mo=)/LC_MESSAGES/bleachbit.mo

install: $(MOFILES)
	for MO in $(MOFILES); do \
		DST=$(DESTDIR)/usr/share/locale/$${MO/.mo/}/LC_MESSAGES/; \
		mkdir -p $$DST; \
		cp $$MO $$DST/bleachbit.mo; \
done

clean:
	@rm -fv *.mo

all: $(APP).pot $(MOFILES)

