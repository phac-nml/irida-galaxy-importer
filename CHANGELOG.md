# Change Log

All notable changes to irida-galaxy-importer will be documeted in this file.

## 2.1.0
* Added in support for importing IRIDA files that are not available locally (i.e. in the cloud)

## 2.0.1
* Switched from travisCI tests to Github Actions
* Switched integration tests to launch irida via gradle

## 2.0.0

* Added support for Python 3, while maintaining Python 2 support
* Removed toolshed installation support
* Changes `--config` option to accept a path to to a config file
* Adds in `--generate_xml` option which is the new option to generate the galaxy tool xml file
* Adds in `tool_id`, `tool_file`, and `tool_description` options to the config file. These options are used to customize the galaxy tool xml file (e.g. for multiple installations of the tool for multiple Irida installs)
* Added in support for importing assemblies and FAST5 data from IRIDA


## 1.4.0

* Migrated all code to GitHub repository.
* Fixed test suite to work with TravisCI.
* Updated documentation for tool.
