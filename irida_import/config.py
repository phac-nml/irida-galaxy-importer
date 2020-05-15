import configparser
import os.path
import re
import shutil

import xml.etree.ElementTree as ET


ET._original_serialize_xml = ET._serialize_xml

def serialize_xml_with_CDATA(write, elem, qnames, namespaces, short_empty_elements, **kwargs):
    if elem.tag == 'CDATA':
        write("<![CDATA[{}]]>".format(elem.text))
        return
    return ET._original_serialize_xml(write, elem, qnames, namespaces, short_empty_elements, **kwargs)

ET._serialize_xml = ET._serialize['xml'] = serialize_xml_with_CDATA

def CDATA(text):
    element = ET.Element("CDATA")
    element.text = text
    return element


class Config:

    """
    Config module for Irida Import tool
    """

    MODULE_DIR = os.path.dirname(os.path.realpath(__file__))

    DEFAULT_CONFIG_FILE = 'config.ini'
    DEFAULT_CONFIG_PATH = os.path.join(MODULE_DIR, DEFAULT_CONFIG_FILE)

    SAMPLE_TOOL_FILE = 'irida_import.xml.sample'
    DEFAULT_TOOL_FILE = 'irida_import.xml'

    def __init__(self, config_file):
        self.CONFIG_FILE = config_file
        self._load_from_file()

    def _load_from_file(self):
        """
        Load the tools configuration from the config file
        """
        with open(self.CONFIG_FILE, 'r') as config_fh:
            config = configparser.ConfigParser()
            config.readfp(config_fh)

            # TODO: parse options from command line and config file as a list
            self.ADMIN_KEY = config.get('Galaxy', 'admin_key')
            self.GALAXY_URL = config.get('Galaxy', 'galaxy_url')
            self.ILLUMINA_PATH = config.get('Galaxy', 'illumina_path')
            self.REFERENCE_PATH = config.get('Galaxy', 'reference_path')
            self.XML_FILE = config.get('Galaxy', 'xml_file')
            self.MAX_WAITS = int(config.get('Galaxy', 'max_waits'))
            self.MAX_RETRIES = 3

            # Used to reconnect to Galaxy instance when connection is lost
            self.MAX_CLIENT_ATTEMPTS = int(config.get('Galaxy', 'max_client_http_attempts'))
            self.CLIENT_RETRY_DELAY = int(config.get('Galaxy', 'client_http_retry_delay'))

            self.TOOL_ID = config.get('Galaxy', 'tool_id', fallback='irida_import')
            self.TOOL_DESCRIPTION = config.get('Galaxy', 'tool_description', fallback='server')
            self.TOOL_FILE = config.get('Galaxy', 'tool_file', fallback='irida_import.xml')

            self.TOKEN_ENDPOINT_SUFFIX = config.get('IRIDA',
                                                    'token_endpoint_suffix')
            self.INITIAL_ENDPOINT_SUFFIX = config.get('IRIDA',
                                                        'initial_endpoint_suffix')

            irida_loc = config.get('IRIDA', 'irida_url')
            self.TOKEN_ENDPOINT = irida_loc + self.TOKEN_ENDPOINT_SUFFIX
            self.IRIDA_ENDPOINT = irida_loc + self.INITIAL_ENDPOINT_SUFFIX

            self.CLIENT_ID = config.get('IRIDA', 'client_id')
            self.CLIENT_SECRET = config.get('IRIDA', 'client_secret')


    def generate_xml(self):
        """
        Generate the tools xml file

        """

        # Configure the tool XML file
        # The Galaxy server must be restarted for XML configuration
        # changes to take effect.
        sample_xml_path = os.path.join(self.MODULE_DIR, self.SAMPLE_TOOL_FILE)
        tree = ET.parse(sample_xml_path)

        tree.getroot().set('id', self.TOOL_ID)

        tree.find('description').text = self.TOOL_DESCRIPTION

        # if the user specified a config file we will add that to the tools command string
        if self.CONFIG_FILE != self.DEFAULT_CONFIG_PATH:
            command_elem = tree.find('command')
            old_command = command_elem.text
            command_elem.text = None
            command_elem.append(CDATA("{}    --config {}\n    ".format(old_command, self.CONFIG_FILE)))

        inputs = tree.find('inputs')
        inputs.set('action', self.IRIDA_ENDPOINT)

        params = inputs.findall('param')
        for param in params:
            if param.get('name') == 'galaxyClientID':
                param.set('value', self.CLIENT_ID)
            # manually set GALAXY_URL instead of using galaxy's baseurl type
            # so that sites with SSL will work
            # https://github.com/phac-nml/irida-galaxy-importer/issues/1
            if param.get('name') == 'galaxyCallbackUrl':
                previous_value = param.get('value')
                param.set('value', re.sub(r'TOOL_ID', self.TOOL_ID, re.sub(r'GALAXY_URL', self.GALAXY_URL, previous_value)))

        tree.write(self.TOOL_FILE)