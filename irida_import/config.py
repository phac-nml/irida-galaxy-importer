import configparser
import os.path
import re
import shutil

from xml.etree import ElementTree


class Config:

    """
    Config module for Irida Import tool
    """

    MODULE_DIR = os.path.dirname(os.path.realpath(__file__))

    CONFIG_FILE = 'config.ini'
    CONFIG_PATH = os.path.join(MODULE_DIR, CONFIG_FILE)

    XML_FILE_SAMPLE = 'irida_import.xml.sample'
    XML_FILE = 'irida_import.xml'

    def __init__(self):
        self._load_from_file()

    def _load_from_file(self):
        """
        Load the tools configuration from the config file
        """
        with open(self.CONFIG_PATH, 'r') as config_file:
            config = configparser.ConfigParser()
            config.readfp(config_file)

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

            self.TOKEN_ENDPOINT_SUFFIX = config.get('IRIDA',
                                                    'token_endpoint_suffix')
            self.INITIAL_ENDPOINT_SUFFIX = config.get('IRIDA',
                                                        'initial_endpoint_suffix')

            irida_loc = config.get('IRIDA', 'irida_url')
            self.TOKEN_ENDPOINT = irida_loc + self.TOKEN_ENDPOINT_SUFFIX
            self.IRIDA_ENDPOINT = irida_loc + self.INITIAL_ENDPOINT_SUFFIX

            self.CLIENT_ID = config.get('IRIDA', 'client_id')
            self.CLIENT_SECRET = config.get('IRIDA', 'client_secret')


    def emit_tool_xml(self):
        """
        Emit the configured tools xml

        """

        src = os.path.join(self.MODULE_DIR, self.XML_FILE_SAMPLE)
        dest = os.path.join(self.MODULE_DIR, self.XML_FILE)
        # Allows storing recommended configuration options in a sample XML file
        # and not commiting the XML file that Galaxy will read:
        try:
            shutil.copyfile(src, dest)
        except:
            pass

        # Configure the tool XML file
        # The Galaxy server must be restarted for XML configuration
        # changes to take effect.
        # The XML file is only changed to reflect the IRIDA URL
        # and IRIDA client ID
        xml_path = os.path.join(self.MODULE_DIR, self.XML_FILE)
        tree = ElementTree.parse(xml_path)

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
                param.set('value', re.sub(r'GALAXY_URL', self.GALAXY_URL, previous_value))

        tree.write(xml_path)