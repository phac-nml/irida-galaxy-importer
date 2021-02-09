"""
Copyright Government of Canada 2015-2020

Written by: National Microbiology Laboratory, Public Health Agency of Canada

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this work except in compliance with the License. You may obtain a copy of the
License at:

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
"""

try:
    # python 3 import
    import configparser
except:
    # python 2 import
    import ConfigParser as configparser

import os.path
import sys
import re

import xml.etree.ElementTree as ET


ET._original_serialize_xml = ET._serialize_xml


def serialize_xml_with_CDATA_py2(write, elem, encoding, qnames, namespaces):
    """
    Serializes xml wrapped in CDATA
    """
    if elem.tag == 'CDATA':
        write("<![CDATA[{}]]>".format(elem.text))
        return
    return ET._original_serialize_xml(write, elem, encoding, qnames, namespaces)


def serialize_xml_with_CDATA_py3(write, elem, qnames, namespaces, short_empty_elements, **kwargs):
    if elem.tag == 'CDATA':
        write("<![CDATA[{}]]>".format(elem.text))
        return
    return ET._original_serialize_xml(write, elem, qnames, namespaces, short_empty_elements, **kwargs)


if sys.version_info[0] < 3:
    ET._serialize_xml = ET._serialize['xml'] = serialize_xml_with_CDATA_py2
else:
    ET._serialize_xml = ET._serialize['xml'] = serialize_xml_with_CDATA_py3


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

    LOCAL_STORAGE = 'local'
    AZURE_STORAGE = 'azure'
    AWS_STORAGE = 'aws'

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

            try:
                self.TOOL_ID = config.get('Galaxy', 'tool_id')
            except:
                self.TOOL_ID = 'irida_import'

            try:
                self.TOOL_DESCRIPTION = config.get('Galaxy', 'tool_description')
            except:
              self.TOOL_DESCRIPTION = "server"

            try:
                self.TOOL_FILE = config.get('Galaxy', 'tool_file')
            except:
                self.TOOL_FILE = 'irida_import.xml'

            self.TOKEN_ENDPOINT_SUFFIX = config.get('IRIDA',
                                                    'token_endpoint_suffix')
            self.INITIAL_ENDPOINT_SUFFIX = config.get('IRIDA',
                                                      'initial_endpoint_suffix')

            irida_loc = config.get('IRIDA', 'irida_url')
            self.TOKEN_ENDPOINT = irida_loc + self.TOKEN_ENDPOINT_SUFFIX
            self.IRIDA_ENDPOINT = irida_loc + self.INITIAL_ENDPOINT_SUFFIX

            self.CLIENT_ID = config.get('IRIDA', 'client_id')
            self.CLIENT_SECRET = config.get('IRIDA', 'client_secret')

            try:
                self.IRIDA_STORAGE_TYPE = config.get('IRIDA', 'irida_storage_type')

                if self.isAzureStorage():
                    self.AZURE_ACCOUNT_NAME = config.get('IRIDA', 'azure_account_name')
                    self.AZURE_ACCOUNT_ENDPOINT= config.get('IRIDA', 'azure_account_endpoint')
                    self.AZURE_SAS_TOKEN = config.get('IRIDA', 'azure_sas_token')
                    self.AZURE_CONTAINER_NAME = config.get('IRIDA', 'azure_container_name')
                if self.isAwsStorage():
                    self.AWS_BUCKET_NAME = config.get('IRIDA', 'aws_bucket_name')
                    self.AWS_ACCESS_KEY = config.get('IRIDA', 'aws_access_key')
                    self.AWS_SECRET_KEY = config.get('IRIDA', 'aws_secret_key')
            except:
                self.IRIDA_STORAGE_TYPE = 'local'

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
            command_elem.text = "{}    --config {}\n    ".format(old_command, self.CONFIG_FILE)

        # rewrap the command_text in a CDATA tag
        command_elem = tree.find('command')
        command_text = command_elem.text
        command_elem.text = None
        command_elem.append(CDATA(command_text))

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
                new_value = re.sub(r'GALAXY_URL', self.GALAXY_URL, previous_value)
                new_value = re.sub(r'TOOL_ID', self.TOOL_ID, new_value)
                param.set('value', new_value)

        tree.write(self.TOOL_FILE)

    def isAzureStorage(self):
        """
        Returns if IRIDA_STORAGE_TYPE is azure

        """
        return self.IRIDA_STORAGE_TYPE == self.AZURE_STORAGE

    def isAwsStorage(self):
        """
        Returns if IRIDA_STORAGE_TYPE is aws

        """
        return self.IRIDA_STORAGE_TYPE == self.AWS_STORAGE

    def isLocalStorage(self):
        """
        Returns if IRIDA_STORAGE_TYPE is local

        """
        return self.IRIDA_STORAGE_TYPE == self.LOCAL_STORAGE