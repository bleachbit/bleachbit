APP = bleachbit
PO = $(wildcard *.po)
MO = $(patsubst %.po,%.mo,$(PO))
SRC = $(wildcard ../bleachbit/*.py)


$(APP).pot : $(SRC)
	xgettext -o $(APP).pot --default-domain=$(APP) $(SRC)

refresh-po:
	#msgmerge bleachbit.pot es.po >es.pot
	#mv es.pot es.po

%.mo: %.po
	msgfmt --statistics -o $@ $<
	mkdir -p echo ../locale/$(@:.mo=)/LC_MESSAGES/
	cp $@ ../locale/$(@:.mo=)/LC_MESSAGES/bleachbit.mo

clean:
	@rm -fv *.mo

all: $(APP).pot $(MO)

