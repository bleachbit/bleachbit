# Copyright (C) 2008-2025 Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: You are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.

# On some systems if not explicitly given, make uses /bin/sh, so 'make pretty' fails.
SHELL := /bin/bash

.PHONY: pretty tests require-xmllint

require-xmllint:
	command -v xmllint >/dev/null 2>&1 || { echo "ERROR: Missing xmllint. APT users, try: sudo apt install libxml2-utils"; exit 1; }

pretty: require-xmllint
	shopt -s nullglob; \
	for f in *xml; \
	do \
		xmllint --format "$$f" > "$$f.pretty"; \
		diff=`diff -q "$$f" "$$f.pretty" | grep -o differ`; \
		[[ "$$diff" != "differ" ]] && echo "$$f" unchanged && rm -- "$$f.pretty"; \
		[[ -s "$$f.pretty" ]] && echo "$$f" is pretty now!!! && mv -- "$$f.pretty" "$$f"; \
	done; \
	exit 0

tests: require-xmllint
	lintrc=0; \
	shopt -s nullglob; \
	for f in *.xml; \
	do \
		xmllint --noout --schema ../doc/cleaner_markup_language.xsd "$$f"; \
		# In case of an error, delay exit, so we can see all errors. \
		lintrc=$$(($$lintrc + $$?)); \
	done; \
	exit $$lintrc
