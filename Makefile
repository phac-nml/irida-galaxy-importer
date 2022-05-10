SHELL=/bin/bash
IRIDA_VERSION?=master

requirements: clean env
	source .virtualenv/bin/activate
	python3 -m pip install -e .

clean:
	rm -rf irida_import/.pytest_cache
	rm -rf .virtualenv
	rm -rf irida_import.egg-info/
	find -name "*pyc" -delete
	rm -rf irida_import/tests/integration/repos

env:
	python3 -m venv .virtualenv
	source .virtualenv/bin/activate
	python3 -m pip install --upgrade wheel pip

unittests: clean env
	source .virtualenv/bin/activate
	pip3 install -e .
	pip3 install pytest
	pytest irida_import/tests/unit/*.py

integrationtests: clean env
	source .virtualenv/bin/activate
	python3 -m pip install -e .[TEST]
	python3 -m pip install pytest
	mkdir irida_import/tests/integration/repos
	python3 irida_import/tests/integration/start_integration_tests.py $(branch) $(db_host) $(db_port)
