#!/bin/bash

# This file is adapted from https://irida.corefacility.ca/gitlab/aaron.petkau/irida-public/blob/master/galaxy/install_galaxy.sh
# which was written by Aaron Petkau


echo "Downloading Galaxy..."
git clone https://github.com/galaxyproject/galaxy/ > galaxy-clone.log 2>&1
pushd galaxy
git fetch --all
git reset --hard 
git clean -fd 
git checkout master > galaxy-checkout.log 2>&1
echo "Preparing Galaxy for first execution (installing eggs)..."
./scripts/common_startup.sh > galaxy-common-startup.log 2>&1

# setup the Galaxy ID secret 
galaxy_id_secret=`pwgen -s 56`


echo "Configuring Galaxy."
pushd config

cp galaxy.ini.sample galaxy.ini
cp tool_conf.xml.sample tool_conf.xml

# allow soft linking of file system files
sed -i 's/#allow_library_path_paste = False/allow_library_path_paste = True/'  galaxy.ini

# allow importing from the entire system
sed -i 's/#library_import_dir.*/library_import_dir = \//'  galaxy.ini

# use MySQL instead of sqlite; to be configured to use a database user and name specified in README.md
sed  -i 's/#database_connection = sqlite:\/\/\/.\/database\/universe.sqlite?isolation_level=IMMEDIATE/database_connection = mysql:\/\/galaxy2:Xuch4pho@localhost\/galaxy2?unix_socket=\/var\/run\/mysqld\/mysqld.sock/' galaxy.ini

# Change Galaxy id_secret used for encoding/decoding database ids to URLs
sed -i "s/#id_secret = .*/id_secret=$galaxy_id_secret/" galaxy.ini

# add uploader/running/admin e-mail user
sed -i 's/#admin_users = None/admin_users=irida@irida.ca/' galaxy.ini

# run galaxy on port 8888 instead of 8080; Tomcat runs on 8080 by default.
sed -i "s|#port = 8080|port = 8888|" galaxy.ini
popd
popd

echo "Installing dependiancies."
pip install -U bioblend pytest pytest-cov pytest-mock requests-oauthlib 

echo "Downloading the IRIDA Export Tool."
git clone git@irida.corefacility.ca:jthiessen/import-tool-for-galaxy.git # > tool-clone.log 2>&1
pushd import-tool-for-galaxy
git fetch --all
git reset --hard origin/development
git clean -fd
git checkout development
popd


echo "Initializing the tool's configuration file."
cp -r import-tool-for-galaxy/irida_import galaxy/tools/
pushd galaxy/tools/irida_import/
cp config.ini.sample config.ini
sed -i "s/.*admin_key:.*/admin_key: $api_key/" config.ini
sed -i "s/PRINT_TOKEN_INSECURELY = False.*/PRINT_TOKEN_INSECURELY = True/" irida_import.py

echo "Configuring the tool's XML file"
python irida_import.py --config
popd

echo "Adding the tool to the Galaxy tool configuration file."
pushd galaxy
pushd config
sed  -i '/<section id="getext" name="Get Data">/a\    <tool file="irida_import/irida_import.xml" />' tool_conf.xml
popd

echo "Starting Galaxy for first run. Run [tail -f /opt/irida/galaxy-dist/galaxy.log] to monitor."
./run.sh > galaxy.log 2>&1 &

echo "Waiting for Galaxy to finish first run initialization..."

while ! bash -c "echo 2> /dev/null > /dev/tcp/localhost/8888" ; do
	echo -n '.'
	sleep 1
done
