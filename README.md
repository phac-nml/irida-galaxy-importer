IRIDA Import Tool for Galaxy
============================

This is a Galaxy tool that imports sequence data from IRIDA to Galaxy.


Install Instructions:
---------------------



#### Initial Instructions

This tool can be installed manually, or it can be archived to be added to Galaxy via a toolshed by running `make_tool_tarball.sh`
In both cases, a tool configuration file will need to be modified, and `galaxy.ini` may need to be modified.

If you are installing from a toolshed, note that because of how Galaxy uses virtualenv,
the tool may attempt to use the wrong versions of libraries.
To fix this, change the line in the `env.sh` that Galaxy creates for the tool that reads something like:
```bash
PYTHONPATH=/home/someuser/shed/irida-galaxy-importer/1.3.0/someuser/irida_export_tool/5d2cb354d0f9/venv/lib/python2.7/site-packages:$PYTHONPATH; export PYTHONPATH 
```
to read:
```bash
PYTHONPATH=/home/someuser/shed/irida-galaxy-importer/1.3.0/someuser/irida_export_tool/5d2cb354d0f9/venv/lib/python2.7/site-packages
```


#### Prerequisites

The BioBlend and Requests-OAuthlib libraries are required. The tool will install them if it is being installed from a toolshed.
They can be manually installed by:

```
pip install bioblend requests-oauthlib
```

You may need to also install the Python and YAML development libraries. On Ubuntu, you can install them with:

```
sudo apt-get install python-dev libyaml-dev
```

If you are using Python 2.6, argparse must be installed too. If you are not installing from a toolshed invoke:

```
pip install argparse
```


#### Tool Installation and Galaxy Configuration:

If the tool is not being added from a toolshed, place the git repository's `irida_import` folder into `$GALAXY_ROOT/tools/`
Then add an entry for irida_import.xml to `$GALAXY_ROOT/config/tool_conf.xml` to the "Get Data" section:

```
<tool file="irida_import/irida_import.xml" />
```

Modify the following lines in galaxy.ini:

```
library_import_dir = /
```

```
allow_library_path_paste = True
```


#### Configuring the Tool:

WARNING: The tool is currently set to ALLOW unsecured connections to IRIDA. This option MUST be disabled if the tool
 will be used over the internet. Set `os.environ['OAUTHLIB_INSECURE_TRANSPORT']` to `0` in `irida_import.py` to disable it, or delete that line.

Note: It is not neccessary to do any of the steps in this subsection in order to run the tests.


The tool reads configuration information from `config.ini`. There is a sample configuration file, `config.ini.sample`.

The location at which the tool expects to find the IRIDA server
can be changed by modifying the following line in the configuration file:

```
irida_url: http://localhost:8080
```

The administrator API key, and the URL of the Galaxy web server must be defined.
Change the values for `admin_key` and `galaxy_url` appropriately.
Instructions for obtaining an API key can be found in the Galaxy documentation.

Modify `client_id` and `client_secret` to values belonging to an IRIDA client.
To find out how to create or view an IRIDA client, consult the IRIDA documentation.
The client must have read scope--auto approval is recomended though not required.

It is also possible to configure the folders in which sample files and reference data are stored, and the endpoints at which the tool
expects to access IRIDA resources.


#### Final Configuration:

The tool must be run once with the `--config` option to configure the tool XML file (`python irida_import.py --config`). Then Galaxy must be restarted if it has not been configured to monitor tools for changes. The tool will fail to export files if Galaxy is not restarted or configured to monitor for changes.



Testing:
-------


#### Running the Tests:

To run the tests, pytest is required.
It can be installed by:

```
pip install -U pytest
```

The Mock library, pytest-mock, subprocess32, and Splinter must be installed as well:

```
pip install -U mock pytest-mock subprocess32 splinter
```

Requests 2.6.2 causes the test setup to fail while uploading sequence files to IRIDA. Use Requests 2.6.0 instead:
```
pip install requests==2.6.0 requests-oauthlib==0.4.2
```

MySQL must be configured to grant all privileges to the user `test` with password `test` for the databases
`irida_test`, and `external_galaxy_test`:

```
echo "grant all privileges on irida_test.* to 'test'@'localhost' identified by 'test';" | mysql -u root -p
echo "grant all privileges on external_galaxy_test.* to 'test'@'localhost' identified by 'test';" | mysql -u root -p
```

Then to run the tests, navigate to `$GALAXY_ROOT/tools/irida_import/` and  invoke:

```
py.test
```

To monitor test progress, for example to monitor the installation and configuration process for the integration tests, use `pytest -s`.

To run only the unit or integration tests, use `pytest -m unit` or `pytest -m integration` respectively.


#### Generating Code Coverage Reports:

First install pytest-cov:

```
pip install pytest-cov
```

Then, to generate a html line by line code coverage report for a file--for example for `irida_import.py`--navigate to `$GALAXY_ROOT/tools/irida_import` and then invoke:

```bash
py.test --cov=irida_import.py --cov-report=html
```
