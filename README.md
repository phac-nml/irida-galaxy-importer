IRIDA import tool for Galaxy
============================

A tool to import data from IRIDA to Galaxy is being implemented here.

Install Instructions:
---------------------

#### Preamble:

and to add itself to `tool_conf.xml`

#### Prerequisites:

This tool requires BioBlend and Requests-OAuthlib. The tool should install them if it is being installed from a toolshed.
They can be manually installed by:

```
pip install bioblend requests-oauthlib
```


#### Initial Installation:

If the tool is not being added from a toolshed, place the git repository's `irida_import` folder into `$GALAXY_ROOT/tools/`
Then add an entry for irida_import.xml to `$GALAXY_ROOT/config/tool_conf.xml` to the "Get Data" section:

```
<tool file="irida_import/irida_import.xml" />
```

If `tool_conf.xml` doesn't exist, you can copy the example version, `tool_conf.xml.sample`
As well, if `galaxy.ini` is missing, you can copy `galaxy.ini.sample`


Modify the following lines in galaxy.ini:

```
library_import_dir = /
```

```
allow_library_path_paste = True
```


#### Configuring IRIDA-Galaxy Communications:

WARNING: The tool is currently set to ALLOW unsecured connections to IRIDA. This option MUST be disabled if the tool
 will be used over the internet. Set `os.environ['OAUTHLIB_INSECURE_TRANSPORT']` to `0` in `irida_import.py` to disable it.

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

Currently the tool uses the webClient client id and secret to access IRIDA. 
They can be changed by modifying `client_id` and `client_secret`

It is also possible to configure the folders in which sample files and reference data are stored, and the endpoints at which the tool
expects to access IRIDA resources.

#### Final Configuration:

The tool must be run once with the `--config` option to configure the tool XML file. Then Galaxy must be restarted if it has not been configured to monitor tools for changes. The tool will fail to export files if Galaxy is not restarted or configured to monitor for changes.

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

To run only the unit or integration tests, use `pytest -m unit` or `pytest -m integration` respectivly.


#### Generating Code Coverage Reports:

Install pytest-cov:

```
pip install pytest-cov
```

To generate a html line by line code coverage report for a file, for example for `irida_import.py`, navigate to `$GALAXY_ROOT/tools/irida_import` and then invoke:

```
py.test --cov=irida_import.py --cov-report=html
```



 
