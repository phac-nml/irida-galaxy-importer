Upgrading
=========

This document summarizes any special instructions that must be followed when upgrading this tool.

1.3.0 - 2.0.0
-------------
NOTE: This upgrade removed Tool Shed installation support, if you had previously installed this tool from a Tool Shed please refer to the updated installation instructions in [README.md](README.md).

If you had previously installed the tool manually from GitHub please follow the instructions below:

Note: We are assuming that you cloned the repo to `galaxy/tools/irida-galaxy-importer`.

Change the following line in `galaxy/config/tool_conf.xml`:

From

```xml
<tool file="irida-galaxy-importer/irida_import/irida_import.xml" />
```

To

```xml
<tool file="irida-galaxy-importer/irida_import.xml" />
```

Now we need to regenerate te tool XML file:

```bash
pushd galaxy/tools/irida-galaxy-importer
python -m irida_import.main --generate_xml
popd
```

At this point you will likely need to restart galaxy so that it can load the new tool XML.

Please ensure that you have all dependencies installed that are listed in [Section 2.1.2](README.md#212-install-dependencies) of the README.MD
