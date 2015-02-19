IRIDA import tool for Galaxy
============================

A tool to import data from IRIDA to Galaxy is being implemented here.

Install Instructions:
---------------------


#### Prerequisites:

This tool requires bioblend 0.5.2. It can be installed by:

```
pip install bioblend`
```

To invoke the import tool from within Galaxy, currently the HTML stub uploader must be used. It requires a web server.


#### Initial Installation:

Place the repository's contents into `$GALAXY_ROOT/tools/irida_import` The directory `irida_import` must be made.

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


#### Setting up the HTML Stub Uploader:

Note: It is not neccessary to do any of the steps in this subsection in order to run the tests.

To use the tool from within Galaxy, right now, by default, the tool looks for a HTML page at `http://localhost:81`
Set up a webserver serving a copy of the HTML page, `irida_import/extras/apache/index.html`. Example config files for Apache2 are included alongside the HTML page.

Cross Origin Resource Sharing (CORS) should be set up, because it likely be required. Galaxy's stripped down paste implementation does not implement CORS, or (to my knowlege) retain an easy way to add it but CORS can be added to a nginx reverse-proxy for Galaxy. A sample configuration file is included: `irida_import/extras/nginx/nginx.conf`
The file assumes that Galaxy can be found on `localhost:8888` Change the occurence of this phrase in the configuration file if your Galaxy instance is located elsewhere.


#### Final Configuration:

The administrator API key, and the URL of the Galaxy web server must be configured. In `$GALAXY_ROOT/tools/irida_import/irida_import.py`, change the values for `ADMIN_KEY` and `GALAXY_URL` appropriately. Instructions for obtaining an API key can be found in the Galaxy documentation.


These installation and configuration steps are planned to be simplified, as simplification becomes possible.


Testing:
-------


#### Running the Tests:

To run the tests, pytest is required.
It can be installed by:

```
pip install -U pytest # or
easy_install -U pytest
```

The mock library must be installed as well:

```
pip install mock
```

Then to run the tests invoke:

```
py.test
```

In addition, one or more of the paths in `$GALAXY_ROOT/tools/irida_import/prelim_json.json` should be modified to point to local files to test uploading with.


#### Generating Code Coverage Reports:

Install pytest-cov:

```
pip install pytest-cov
```

To generate a html line by line code coverage report for a file, for example for `irida_import.py`, navigate to `$GALAXY_ROOT/tools/irida_import` and then invoke:

```
py.test --cov=irida_import.py --cov-report=html
```




