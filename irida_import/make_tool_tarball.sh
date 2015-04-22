#!/bin/bash
cp ../README.md README.md
cp irida_import.xml.sample irida_import.xml
tar -cvzf ../irida_import_tool.tar.gz README.md irida_import.xml irida_import.xml.sample config.ini.sample sample_file.py sample.py tool_dependencies.xml irida_import.py 
rm README.md
