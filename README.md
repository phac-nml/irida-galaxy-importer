IRIDA import tool for Galaxy
============================

A tool to import data from IRIDA to Galaxy is being implemented here.

Install Instructions:
---------------------


#### Prerequisites:

This tool requires BioBlend and Requests-OAuthlib. They can be installed by:

```
pip install bioblend requests-oauthlib
```


#### Initial Installation:

Place the repository's `irida_import` folder into `$GALAXY_ROOT/tools/`
Add an entry for irida_import.xml to `$GALAXY_ROOT/config/tool_conf.xml` to the "Get Data" section:

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

The tool currently uses the webClient client id and secret to access IRIDA. 
They can be changed by modifying `client_id` and `client_secret`

It is also possible to configure the folders in which sample files and reference data are stored, and the endpoints at which the tool
expects to access IRIDA resources.

Cross Origin Resource Sharing (CORS) should be set up, because it may be required. Galaxy's stripped down paste implementation does not implement CORS, or (to my knowlege) retain an easy way to add it but CORS can be added to a nginx reverse-proxy for Galaxy. A sample configuration file is included: `irida_import/extras/nginx/nginx.conf`
The nginx configuration file assumes that Galaxy can be found on `localhost:8888` Change the occurence of this phrase in the configuration file if your Galaxy instance is located elsewhere.


#### Final Configuration:

The tool must be run once with the `--config` option to configure the tool XML file. Then Galaxy must be restarted. The tool will fail to export files if Galaxy is not restarted.

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




