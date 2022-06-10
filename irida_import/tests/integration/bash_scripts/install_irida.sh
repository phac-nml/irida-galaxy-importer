#!/bin/bash

pushd /tmp/repos

echo "Downloading IRIDA..."
if ! git clone https://github.com/phac-nml/irida.git --branch $1
then
    echo >&2 "Failed to clone"
    exit 1
else
  pushd irida
  echo "Preparing IRIDA for first excecution..."

  pushd lib
  ./install-libs.sh
  popd
  popd
  echo "IRIDA has been installed"
fi
