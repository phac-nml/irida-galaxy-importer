SHELL=/bin/bash
IRIDA_VERSION?=master

requirements: clean env
	source .virtualenv/bin/activate
	pip3 install -e .

clean:
	rm -rf irida_import/.pytest_cache
	rm -rf .virtualenv
	rm -rf irida_import.egg-info/
	find -name "*pyc" -delete
# 	rm -rf iridauploader/tests_integration/repos/
# 	rm -rf iridauploader/tests_integration/tmp

env:
	python3 -m venv .virtualenv
	source .virtualenv/bin/activate
	pip3 install --upgrade wheel pip

unittests: clean env
	source .virtualenv/bin/activate
	pip3 install -e .
	pip3 install pytest
	pytest irida_import/tests/unit/*.py
