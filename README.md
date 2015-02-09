A tool to import data from IRIDA to Galaxy will is being implemented here.

Install Instructions:

Place all the files in the irida_import directory in the Galaxy tools directory

Add an entry for irida_import.xml to tool_conf.xml:
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

Also, change the string '/home/jthiessen/galaxy-dist/tools/irida_import/prelim_json.json' in irida_import.py to be the location that prelim_json.json is on your system. In addition, one or more of the paths in prelim_json.json should be modified to point to local files to test uploading with. 

These configuration steps are planned to be simplified, as simplification becomes possible.

