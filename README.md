IRIDA import tool for Galaxy
============================

A tool to import data from IRIDA to Galaxy is being implemented here.

Install Instructions:
---------------------


#### Prerequisites:

This tool requires bioblend 0.5.2. It can be installed by:

`pip install bioblend`

The mock library must be installed as well:

`pip install mock`

To invoke the import tool from within Galaxy, currently the HTML stub uploader must be used. It requires a web server.


#### Initial Installation:

Place the repository's contents into `$GALAXY_ROOT/tools/irida_import` The directory `irida_import` must be made.

Add an entry for irida_import.xml to `$GALAXY_ROOT/config/tool_conf.xml` to the "Get Data" section:

`<tool file="irida_import/irida_import.xml" />`

If `tool_conf.xml` doesn't exist, you can copy the example version, `tool_conf.xml.sample`
As well, if `galaxy.ini` is missing, you can copy `galaxy.ini.sample`

Modify the following lines in galaxy.ini:

`library_import_dir = /`

`allow_library_path_paste = True`


#### Setting up the HTML Stub Uploader:

Note: It is not neccessary to do any of the steps in this subsection in order to run the tests.

To use the tool from within Galaxy, right now, by default, the tool looks for a HTML page at `http://localhost:80`
The HTML page must be configured to `POST` to an address consisting of the Galaxy instance's domain + `/tool_runner?tool_id=irida_import&amp;runtool_btn=Execute` The full address is passed by Galaxy to the HTML page as the parameter `GALAXY_URL`

An example HTML file is included. Place it in your web server's root directory, or set the tool to look for the HTML page at a custom address by modifying the `action` key's value in `irida_import/irida_import.xml`:

`<inputs action="http://localhost:80" check_values="False" method="post">`

If your Galaxy instance supports CORS it will automatically use jQuery to `POST`, otherwise just click the button to send via the `action` of a HTML form.
It is a good idea to configure CORS for the Galaxy instance: this is planned to become a requirement soon.
Configuration instructions for CORS for the default Galaxy web sever will be added when they are known.

In addition, change the string `/home/jthiessen/galaxy-dist/tools/irida_import/prelim_json.json` in `irida_import.py` to be the location that `prelim_json.json` is on your system.  

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

To run the tests, invoke:

`py.test`

In addition, one or more of the paths in `$GALAXY_ROOT/tools/irida_import/prelim_json.json` should be modified to point to local files to test uploading with.


#### Generating Code Coverage Reports:

Install pytest-cov:

`pip install pytest-cov`

To generate a html line by line code coverage report for a file, for example for `irida_import.py`, navigate to `$GALAXY_ROOT/tools/irida_import` and then invoke:

`py.test --cov=irida_import.py --cov-report=html`
