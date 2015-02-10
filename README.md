IRIDA import tool for Galaxy
============================

A tool to import data from IRIDA to Galaxy is being implemented here.

Install Instructions:
---------------------

###Initial Installation:

Place all the files in the irida_import directory in the Galaxy tools directory.

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

###Setting up the HTML stub uploader:

To use the tool from within Galaxy, right now, by default, the tool looks for a HTML page at `http://localhost:80`
The HTML page must be set to `POST` to an address consisting of the Galaxy instance's domain + `/tool_runner?tool_id=irida_import&amp;runtool_btn=Execute` This address is passed by Galaxy to the HTML page as the parameter `GALAXY_URL`

An example HTML file is included. Place it in your webserver's root directory, or set the tool to look for the HTML page at a custom address by modifying the `action` key's value in `irida_import/irida_import.xml`:

```
<inputs action="http://localhost:80" check_values="False" method="post">
```

If your Galaxy instance supports CORs it will automatically use jQuery to `POST`, otherwise just click the button to send via the `action` of a HTML form.


###Running the tests:

To run the tests, pytest is required.
It can be installed by:

```
pip install -U pytest # or
easy_install -U pytest
```

To run the tests, invoke:
```
py.test
```

In addition, one or more of the paths in prelim_json.json should be modified to point to local files to test uploading with. 


To run the tool from Galaxy, change the string '/home/jthiessen/galaxy-dist/tools/irida_import/prelim_json.json' in irida_import.py to be the location that prelim_json.json is on your system. It is not neccessary to do this to run the tests. 


These configuration steps are planned to be simplified, as simplification becomes possible.

