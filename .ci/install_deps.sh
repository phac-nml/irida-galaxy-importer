#!/bin/bash -e

CHROMEDRIVER_VERSION=$1

#some setup of bioconda 'borrowed' from https://github.com/bioconda/bioconda-recipes/tree/master/.circleci
WORKSPACE=`pwd`

wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p $WORKSPACE/miniconda

# step 2: setup channels
$WORKSPACE/miniconda/bin/conda config --system --add channels defaults
$WORKSPACE/miniconda/bin/conda config --system --add channels bioconda
$WORKSPACE/miniconda/bin/conda config --system --add channels conda-forge


# Set path
echo "export PATH=\"$WORKSPACE/miniconda/bin:$PATH\"" >> $BASH_ENV
source $BASH_ENV

#create conda env as Galaxy would
conda create -y --quiet --override-channels --channel iuc --channel conda-forge --channel bioconda --channel defaults --name irida_importer bioblend=0.13.0 oauthlib=3.0.1 requests=2.22.0 requests-oauthlib=1.2.0 simplejson=3.8.1 python=3.6.7

conda activate irida_importer
pip install -U pytest pytest-cov pytest-mock selenium

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
