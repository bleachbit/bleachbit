
clean:
	python setup.py clean

install: build
	python setup.py install -O1 --skip-build --root $(DESTDIR)
	make -C po install DESTDIR=$(DESTDIR)

tests:
	cd bleachbit && grep -l unittest *py | xargs -L 1 python

build:
	python setup.py build
