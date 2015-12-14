#!/bin/bash

# This file is adapted from https://irida.corefacility.ca/gitlab/aaron.petkau/irida-public/blob/master/galaxy/install_galaxy.sh

args=("$@")
tool_loc=${args[0]}
galaxy_port=${args[1]}

mkdir repos
pushd repos

echo "Downloading IRIDA..."
git clone http://gitlab-ci-token:b71f6552f4cbe6f7d3f6faad8939b9@irida.corefacility.ca/gitlab/irida/irida.git
pushd irida
git checkout UI/ja/remove-large-checkbox > irida-checkout.log 2>&1
git fetch
git reset --hard
git clean -fd
git pull
echo "Preparing IRIDA for first excecution..."
rm -rf /tmp/shed_tools/
pkill -u gitlab_ci_runner -f "python ./scripts/paster.py" || true

pushd lib
./install-libs.sh
popd
popd
echo "IRIDA has been installed"

echo "Downloading Galaxy..."
git clone https://github.com/galaxyproject/galaxy/ > galaxy-clone.log 2>&1
pushd galaxy
git checkout master > galaxy-checkout.log 2>&1
git fetch
git reset --hard
git clean -fd
git pull
echo "Preparing Galaxy for first execution (installing eggs)..."
./scripts/common_startup.sh > galaxy-common-startup.log 2>&1

echo "Configuring Galaxy."
pushd config

cp galaxy.ini.sample galaxy.ini
cp tool_conf.xml.sample tool_conf.xml

# allow soft linking of file system files
sed -i 's/#allow_library_path_paste = False/allow_library_path_paste = True/'  galaxy.ini

# allow importing from the entire system
sed -i 's/#library_import_dir.*/library_import_dir = \//'  galaxy.ini

# use MySQL instead of sqlite; to be configured to use a database user and name specified in README.md
sed  -i 's/#database_connection = sqlite:\/\/\/.\/database\/universe.sqlite?isolation_level=IMMEDIATE/database_connection = mysql:\/\/test:test@localhost\/external_galaxy_test?unix_socket=\/var\/run\/mysqld\/mysqld.sock/' galaxy.ini

# add admin e-mail user
sed -i 's/#admin_users = None/admin_users=irida@irida.ca/' galaxy.ini

# run galaxy on port 8888 instead of 8080; Tomcat runs on 8080 by default.
sed -i "s|#port = 8080|port = $galaxy_port|" galaxy.ini
popd
popd
echo "Galaxy has been installed"

echo "Installing the IRIDA Export Tool..."
echo "Copying tool directory"
rsync -rv --progress $tool_loc galaxy/tools --exclude tests

echo "Initializing the tool's configuration file."
pushd galaxy/tools/irida_import/
cp config.ini.sample config.ini

echo "Configuring the tool's XML file"
python irida_import.py --config
popd

echo "Adding the tool to Galaxy's tools configuration file."
pushd galaxy
pushd config
sed  -i '/<section id="getext" name="Get Data">/a\    <tool file="irida_import/irida_import.xml" />' tool_conf.xml
popd

popd

echo "IRIDA, Galaxy, and the IRIDA export tool have been installed"
