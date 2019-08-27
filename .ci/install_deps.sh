#!/bin/bash -e

CHROMEDRIVER_VERSION=$1
python3 -m pip install virtualenv
python3 -m virtualenv .venv
source .venv/bin/activate
pip3 install -U bioblend pytest pytest-cov pytest-mock requests requests-oauthlib subprocess32 selenium

# Install chromedriver if not correct version
TEST_CHROMEDRIVER_VERSION=`chromedriver --version | sed -e 's/^ChromeDriver //' -e 's/ (.*//' 2>/dev/null`
if [ "$TEST_CHROMEDRIVER_VERSION" != "$CHROMEDRIVER_VERSION" ];
then
	echo "Downloading Chromedriver Version: $CHROMEDRIVER_VERSION"
	wget --no-verbose -O /tmp/chromedriver_linux64.zip https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip
	unzip /tmp/chromedriver_linux64.zip -d .venv/bin
	chmod 755 .venv/bin/chromedriver
else
	echo "Chromedriver version [" $CHROMEDRIVER_VERSION "] already exists, not installing"
fi
