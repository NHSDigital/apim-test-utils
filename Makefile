SHELL := /bin/bash
########################################################################################################################
## app e2e tests
########################################################################################################################
pwd := ${PWD}
dirname := $(notdir $(patsubst %/,%,$(CURDIR)))
activate = poetry run

list:
	@grep '^[^#[:space:]].*:' Makefile

guard-%:
	@ if [ "${${*}}" = "" ]; then \
		echo "Environment variable $* not set"; \
		exit 1; \
	fi

install:
	poetry install

clean:
	rm -Rf dist

dist: clean
	poetry build



lint:
	$(activate) pylint --output-format=parseable --rcfile=pylint.rc api_test_utils tests

test:
	$(activate) pytest

coverage:
	rm -f reports/tests.xml  > /dev/null || true
	$(activate) coverage run --source ./ --module pytest -rxs -v --junit-xml=reports/tests.xml --ignore .venv || true
	@if [[ ! -f reports/tests.xml ]]; then echo report not created; exit 1; fi