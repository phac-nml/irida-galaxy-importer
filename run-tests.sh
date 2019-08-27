#!/bin/bash
cd `dirname $0`
SCRIPT_DIR=`pwd`

CHROMEDRIVER_VERSION=''

exit_error() {
        echo $1
        exit 1
}

check_dependencies() {
	mvn --version 1>/dev/null 2>/dev/null
	if [ $? -ne 0 ];
	then
		exit_error "Command 'mvn' does not exist.  Please install Maven (e.g., 'apt-get install maven') to continue."
	fi

	mysql --version 1>/dev/null 2>/dev/null
	if [ $? -ne 0 ];
	then
		exit_error "Command 'mysql' does not exist.  Please install MySQL/MariaDB (e.g., 'apt-get install mariadb-client mariadb-server') to continue."
	fi

	psql --version 1>/dev/null 2>/dev/null
	if [ $? -ne 0 ];
	then
		exit_error "Command 'psql' does not exist.  Please install PostgreSQL (e.g., 'apt-get install postgresql') to continue."
	fi

	python2 --version 1>/dev/null 2>/dev/null
	if [ $? -ne 0 ];
	then
		exit_error "Command 'python2' does not exist.  These tests require python2. Please install (e.g., 'apt-get install python2.7') to continue."
	fi

	git --version 1>/dev/null 2>/dev/null
	if [ $? -ne 0 ];
	then
		exit_error "Command 'git' does not exist.  Please install git (e.g., 'apt-get install git') to continue."
	fi

	chromedriver --version 1>/dev/null 2>/dev/null
	if [ $? -ne 0 ];
	then
		exit_error "Command 'chromedriver' does not exist.  Please install Chromedriver (e.g., 'apt-get install chromium-chromedriver') to continue."
	else
		CHROMEDRIVER_VERSION=`chromedriver --version | sed -e 's/^ChromeDriver //' -e 's/ (.*//' 2>/dev/null`
	fi

	xvfb-run -h 1>/dev/null 2>/dev/null
	if [ $? -ne 0 ];
	then
		exit_error "Command 'xvfb' does not exist.  Please install xvfb (e.g., 'apt-get install xvfb') to continue."
	fi
}

#################
#### MAIN #######
#################

check_dependencies

source $SCRIPT_DIR/.ci/install_deps.sh $CHROMEDRIVER_VERSION

pushd irida_import

# If xvfb is already started, don't bother with 'xvfb-run'. Useful for TravisCI tests.
if [ "$XVFB_STARTED" = "1" ];
then
	py.test -s
else
	xvfb-run py.test -s
fi
