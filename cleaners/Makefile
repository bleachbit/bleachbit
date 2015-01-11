# On some systems if not explicitly given, make uses /bin/sh, so 'make pretty' fails.
SHELL := /bin/bash

PHONY: pretty tests


pretty:
	for f in *xml; \
	do \
		xmllint --format "$$f"  > "$$f.pretty"; \
		diff=`diff -q "$$f" "$$f.pretty" | grep -o differ`; \
		[[ "$$diff" != "differ" ]] && echo "$$f" unchanged && rm "$$f.pretty"; \
		[[ -s "$$f.pretty" ]] && echo "$$f" is pretty now!!! && mv "$$f.pretty" "$$f" ; \
	done; \
	exit 0

tests:
	lintrc=0; \
	for f in *.xml; \
	do \
		xmllint --noout --schema ../doc/cleaner_markup_language.xsd "$$f"; \
		lintrc=$$(($$lintrc + $$?)); \
	done; \
	exit $$lintrc

