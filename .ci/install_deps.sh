#!/bin/bash -e

CHROMEDRIVER_VERSION=$1
PYTHON_VERSION=$2

#some setup of bioconda 'borrowed' from https://github.com/bioconda/bioconda-recipes/tree/master/.circleci
CONDA_ENV="__irida_importer_py${PYTHON_VERSION}"

# check if conda is available
conda --version 2>/dev/null 1>/dev/null
if [ $? -ne 0 ];
then
  WORKSPACE=`pwd`
  BASH_ENV=`mktemp`

  # Set path
  echo "export PATH=\"$WORKSPACE/miniconda/bin:$PATH\"" >> $BASH_ENV
  source $BASH_ENV

  # check if we already installed conda to $WORKSPACE/miniconda
  conda --version 2>/dev/null 1>/dev/null
  if [ $? -ne 0 ];
  then
    echo "Installing conda"

    curl -L -o miniconda.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    bash miniconda.sh -b -p $WORKSPACE/miniconda
  fi
fi

# check for conda environment
conda list -n $CONDA_ENV 2>/dev/null 1>/dev/null
if [ $? -ne 0 ];
then
  echo "Installing conda environment $CONDA_ENV"


  conda create -y --quiet --override-channels --channel iuc --channel conda-forge --channel bioconda --channel defaults --name $CONDA_ENV bioblend=0.13.0 oauthlib=3.0.1 requests=2.22.0 requests-oauthlib=1.2.0 simplejson=3.8.1 python=$PYTHON_VERSION pip

  source activate $CONDA_ENV
  pip install pytest pytest-cov pytest-mock mock subprocess32 selenium boto azure-storage-blob==2.1.0 boto3
else
  source activate $CONDA_ENV
fi

# Install chromedriver if not correct version
TEST_CHROMEDRIVER_VERSION=`chromedriver --version | sed -e 's/^ChromeDriver //' -e 's/ (.*//' 2>/dev/null`
if [ "$TEST_CHROMEDRIVER_VERSION" != "$CHROMEDRIVER_VERSION" ];
then
	echo "Downloading Chromedriver Version: $CHROMEDRIVER_VERSION"
	wget --no-verbose -O /tmp/chromedriver_linux64.zip https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip
	pythonbin=`which python`
	bindir=`dirname $pythonbin`
	unzip /tmp/chromedriver_linux64.zip -d $bindir
	chmod 755 $bindir/chromedriver
else
	echo "Chromedriver version [" $CHROMEDRIVER_VERSION "] already exists, not installing"
fi
