#!/bin/bash
# This file creates a repos directory and pulls the irida branch with the name in $1

pushd /tmp/repos

echo "Downloading IRIDA..."
if ! git clone https://github.com/phac-nml/irida.git --branch $1
then
    echo >&2 "Failed to clone"
    exit 1
else
  echo "IRIDA has been installed"
fi
