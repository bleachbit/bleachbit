
clean:
	python setup.py clean

install: build
	python setup.py install -O1 --skip-build --root $(DESTDIR)
	make -C po install DESTDIR=$(DESTDIR)

build:
	python setup.py build
