PHONY: pretty tests


pretty:
	for f in *xml; \
	do \
		xmllint --format "$$f"  > "$$f.pretty"; \
		diff=`diff -q "$$f" "$$f.pretty" | grep -o differ`; \
		[[ "$$diff" != "differ" ]] && echo "$$f" unchanged && rm "$$f.pretty"; \
		[[ -s "$$f.pretty" ]] && echo "$$f" is pretty now!!! && mv "$$f.pretty" "$$f" ; \
	done

tests:
	for f in *xml; \
	do \
		xmllint --noout --schema ../doc/cleaner_markup_language.xsd "$$f"; \
	done \

