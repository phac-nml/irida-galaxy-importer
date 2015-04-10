#!/bin/bash
virtualenv env
source env/bin/activate
pip install -U bioblend pytest pytest-cov pytest-mock requests-oauthlib subprocess32 splinter
cd irida_import
xvfb-run py.test -s
deactivate

