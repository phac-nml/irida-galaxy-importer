#!/bin/bash

pip install -U bioblend pytest pytest-cov pytest-mock requests-oauthlib subprocess32 splinter
cd irida_import
xvfb-run py.test -s
