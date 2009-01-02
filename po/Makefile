APP = bleachbit
POFILES = $(wildcard *.po)
MOFILES = $(patsubst %.po,%.mo,$(POFILES))
SRC = $(wildcard ../bleachbit/*.py)


$(APP).pot : $(SRC)
	xgettext -o $(APP).pot --default-domain=$(APP) $(SRC)

refresh-po:
	#msgmerge bleachbit.pot es.po >es.pot
	#mv es.pot es.po

%.mo: %.po
	msgfmt --statistics -o $@ $<
	# copy locally for running without installation
	mkdir -p echo ../locale/$(@:.mo=)/LC_MESSAGES/
	cp $@ ../locale/$(@:.mo=)/LC_MESSAGES/bleachbit.mo

install: $(MOFILES)
	@for MO in $(MOFILES); do \
		DST=$(DESTDIR)/usr/share/locale/$${MO/.mo/}/LC_MESSAGES/; \
		mkdir -p $$DST; \
		cp $$MO $$DST/bleachbit.mo; \
done

clean:
	@rm -fv *.mo

all: $(APP).pot $(MOFILES)

