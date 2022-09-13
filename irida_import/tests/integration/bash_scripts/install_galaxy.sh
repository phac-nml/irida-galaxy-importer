#!/bin/bash

args=("$@")
tool_loc=${args[0]}
galaxy_port=${args[1]}

pushd /tmp/repos

echo "Downloading Galaxy..."
git clone https://github.com/galaxyproject/galaxy/ > galaxy-clone.log 2>&1
pushd galaxy
git checkout v22.01 > galaxy-checkout.log 2>&1
git fetch
git reset --hard
git clean -fd
git pull
echo "Preparing Galaxy for first execution (installing eggs)..."
./scripts/common_startup.sh > galaxy-common-startup.log 2>&1

# reset galaxy psql db
echo "dropping galaxy_test database in psql"
echo "drop database if exists galaxy_test; create database galaxy_test;" | psql

echo "Configuring Galaxy."
pushd config

cp galaxy.yml.sample galaxy.yml
cp tool_conf.xml.sample tool_conf.xml

# allow soft linking of file system files
sed -i 's/#allow_path_paste: false/allow_path_paste: true/' galaxy.yml

# allow importing from the entire system
sed -i 's/#library_import_dir.*/library_import_dir: \//'  galaxy.yml

# use MySQL instead of sqlite; to be configured to use a database user and name specified in README.md
echo "  database_connection: postgresql:///galaxy_test" | cat >> galaxy.yml

# add admin e-mail user
sed -i 's/#admin_users:.*/admin_users: "irida@irida.ca"/' galaxy.yml

# run galaxy on port 8888 instead of 8080; Tomcat runs on 8080 by default.
sed -i "s|# bind: localhost:8080|bind: 127.0.0.1:$galaxy_port|" galaxy.yml

popd
popd
echo "Galaxy has been installed"

echo "Installing the IRIDA Export Tool..."
echo "Copying tool directory"
rsync -rv --progress $tool_loc galaxy/tools/irida-galaxy-importer --exclude tests

echo "Initializing the tool's configuration file."
pushd galaxy/tools/irida-galaxy-importer/
cp irida_import/config.ini.sample irida_import/config.ini
sed -i "s/^max_waits: .*$/max_waits: 1/" irida_import/config.ini
sed -i "s|^galaxy_url: http://localhost:8888$|galaxy_url: http://127.0.0.1:$galaxy_port|" irida_import/config.ini

echo "Configuring the tool's XML file"
python -m irida_import.main --generate_xml
popd

echo "Adding the tool to Galaxy's tools configuration file."
pushd galaxy
pushd config
sed  -i '/<section id="getext" name="Get Data">/a\    <tool file="irida-galaxy-importer/irida_import.xml" />' tool_conf.xml
popd

popd

echo "Galaxy and the IRIDA export tool have been installed"
