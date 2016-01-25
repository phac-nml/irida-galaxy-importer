import argparse
import ConfigParser
import datetime
import json
import logging
import os.path
import pprint
import re
import shutil
import sys
import time

from xml.etree import ElementTree

from bioblend import galaxy
from bioblend.galaxy.objects import GalaxyInstance
from requests_oauthlib import OAuth2Session

from sample import Sample
from sample_file import SampleFile
from sample_pair import SamplePair

# FOR DEVELOPMENT ONLY!!
# This value only exists for this process and processes that fork from it
# (none)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Print the token so that it can be used to call the tool from the command line
PRINT_TOKEN_INSECURELY = False


class IridaImport:

    """
    Imports sample's sample files from IRIDA.

    An appropriate library and folders are created if necessary
    """

    CONFIG_FILE = 'config.ini'
    XML_FILE_SAMPLE = 'irida_import.xml.sample'
    XML_FILE = 'irida_import.xml'
    CLIENT_ID_PARAM = 'galaxyClientID'
    CURRENT_LIBRARY_STATE = False
    
    def __init__(self):
        self.logger = logging.getLogger('irida_import')

    def get_samples(self, samples_dict):
        """
        Gets sample objects from a dictionary.

        :type samples_dict: dict
        :param samples_dict: a dictionary to parse. See one of the test
        json files for formatting information (the format will likely
        change soon)
        :return: a list of Samples with all necessary information
        """
        samples = self.get_sample_meta(samples_dict)

        for sample in samples:

            # Add a tuple of sample_file objects for each pair
            paired_resource = self.make_irida_request(sample.paired_path)
            for pair in paired_resource['resources']:
                pair_name = str(pair['identifier'])
                for link in pair['links']:
                    temp_link = dict()
                    temp_link['rel'] = "self"
                    temp_link["href"] = link['href']

                    for curr_file in pair['files']:
                        if temp_link in curr_file['links']:
                            if link['rel'] == "pair/forward":
                                forward = self.get_sample_file(curr_file)
                            elif link['rel'] == "pair/reverse":
                                reverse = self.get_sample_file(curr_file)

                sample.add_pair(SamplePair(pair_name, forward, reverse))

            # Add a sample_file object for each single end read
            unpaired_resource = self.make_irida_request(sample.unpaired_path)
            for single in unpaired_resource['resources']:
                sample.add_file(self.get_sample_file(single))

        return samples

    def make_irida_request(self, request_url):
        """
        Requests json object from IRIDA REST API.

        :type request_url: str
        :param request_url: a url to make a get request to. See IRIDA REST API
        docs for more information
        :return: a list of either single output samples(string) or paired
        output samples(tuple)
        """
        response = self.irida.get(request_url)

        # Raise an exception if we get 4XX or 5XX server response
        response.raise_for_status()

        resource = response.json()['resource']
        self.logger.debug("The JSON parameters from the IRIDA API are:\n" +
                          self.pp.pformat(json.dumps(dict(resource), indent=2)))

        return resource

    def get_sample_meta(self, samples_dict):
        """
        Gets Sample object meta information.

        :type samples_dict: dict
        :param samples_dict: a dictionary to parse. See one of the test
        json files for formating information (the format will likely
        change soon)
        :return: a list of Sample objects with it's name and paired/unpaired
        path
        """
        samples = []

        for sample_input in samples_dict:
            sample_dir_paths = sample_input['_embedded']['sample_files']
            sample_name = sample_input['name']

            for sample_file_path in sample_dir_paths:
                sample_path = sample_file_path['_links']['self']['href']

            sample_resource = self.make_irida_request(sample_path)
            paths = sample_resource['links']
            paired_path = ""
            unpaired_path = ""

            for link in paths:
                if link['rel'] == "sample/sequenceFiles/pairs":
                    paired_path = link['href']
                elif link['rel'] == "sample/sequenceFiles/unpaired":
                    unpaired_path = link['href']

            samples.append(Sample(sample_name, paired_path, unpaired_path))

        return samples

    def get_sample_file(self, file_dict):
        """
        From a dictionary, get file information

        :type file_dict: dict
        :param file_dict: the URL to get the sample file representation
        :return: a sample file with a name and path
        """
        resource = file_dict
        name = resource['fileName']
        path = resource['file']

        return SampleFile(name, path)

    def get_first_or_make_lib(self, desired_lib_name, email):
        """"
        Get or if neccessary create a library that matches a given name.

        :type desired_lib_name: str
        :param desired_lib_name: the desired library name
        :type email: str
        :param email: the email of the Galaxy user to get or make a library for
        :rtype: :class:`~.LibraryDataset`
        :return: the obtained or created library

        This method should never make a library with the same name as an
        already existing library that is accessible using the administrator
        API key

        """
        lib = None
        libs = self.gi.libraries.list(name=desired_lib_name)
        if len(libs) > 0:
            lib = next(lib_i for lib_i in libs if lib_i.deleted is False)

        if(lib is None):
            roles = self.reg_gi.roles.get_roles()
            rid = 0
            try:
                rid = next(role['id']
                           for role in roles if role['name'] == email)
            except StopIteration:
                error = "No Galaxy role could be found for the email: '{0}', "\
                    "quitting".format(email)
                raise Exception(error)

            lib = self.gi.libraries.create(desired_lib_name)
            self.reg_gi.libraries.set_library_permissions(
                lib.id, access_in=[rid], modify_in=[rid], add_in=[rid])
        return lib

    def create_folder_if_nec(self, folder_path):
        """
        Add a folder to a library, if it does not already exist.

        :type folder_path: str
        :param folder_path: The folder's path e.g. '/bobfolder/bobfolder2'
        """
        made_folder = None
        # Get the folder name from the path, e.g. 'bobfolder2' from
        # '/bobfolder/bobfolder2'
        folder_name = folder_path.rsplit("/", 1)[1]
        # Get the base folder path from the path e.g '/bobfolder' from
        # '/bobfolder/bobfolder2'
        base_folder_path = folder_path.rsplit("/", 1)[0]
        self.logger.debug(
            'If neccessary, making a folder named \'%s\' on base folder path'
            '\'%s\' from folder path \'%s\'' %
            (folder_name, base_folder_path, folder_path))

        if not self.exists_in_lib('folder', 'name', folder_path):

            base_folder_list = self.reg_gi.libraries.get_folders(
                self.library.id,
                name=base_folder_path)

            if len(base_folder_list) > 0:
                base_folder = self.library.get_folder(
                    base_folder_list[0]['id'])
                made_folder = self.library.create_folder(
                    folder_name,
                    base_folder=base_folder)
            elif base_folder_path == '':
                made_folder = self.library.create_folder(folder_name)
            else:
                raise IOError('base_folder_path must include an existing base '
                              + 'folder, or nothing')
            self.logger.debug(
                'Made folder with path:' + '\'%s\'' % folder_path)
        return made_folder

    def exists_in_lib(self, item_type, item_attr_name, desired_attr_value):
        """
        Find if an item of given type and attribute exists in the library

        :type item_type: str
        :param item_type: the item type e.g "folder" or "file"
        :type item_attr_name: str
        :param item_attr_name: the item attribute e.g "name"
        :type desired_attr_value: str
        :param desired_attr_value: the desired attribute value e.g "Bob"

        :rtype: Boolean
        :return: whether the item exists in the library
        """
        ans = False

        # check cache before fetching from galaxy.
        # current state of the library should only change between irida_import.py invocation
        if not self.CURRENT_LIBRARY_STATE:
            self.library = self.gi.libraries.get(self.library.id)
            CURRENT_LIBRARY_STATE=True
                                            
        
        # check for an object of the desired type with the desired attribute
        self.library = self.gi.libraries.get(self.library.id)
        for con_inf in self.library.content_infos:
            if con_inf.type == item_type:
                attr = getattr(con_inf, item_attr_name)
                if attr == desired_attr_value:
                    ans = True
                    break
        return ans

    def unique_file(self, sample_file_path, galaxy_name):
        """
        Find out if a sample file is unique

        :type sample_file_path: str
        :param sample_file_path: the local file path to the file to check
        :type galaxy_name: str
        :param galaxy_name: the full path to the sample file as it would
        exist in Galaxy
        :rtype: Boolean
        :return: whether a file with this name and size does not exist in
        Galaxy
        """
        self.logger.debug(
            "Doing a basic check for already existing sample file at: " +
            galaxy_name)
        unique = True
        size = os.path.getsize(sample_file_path)
        self.library = self.gi.libraries.get(self.library.id)
        datasets = self.library.get_datasets(name=galaxy_name)
        for dataset in datasets:
            # Galaxy sometimes appends a newline, see:
            # https://bitbucket.org/galaxy/galaxy-dist/src/
            # 7e4d21621ce12e13ebbdf9fd3259df58c3ef124c/lib/
            # galaxy/datatypes/data.py?at=stable#cl-673
            if dataset.file_size in (size, size + 1):
                unique = False
                break

        return unique

    def existing_file(self, sample_file_path, galaxy_name):
        """
        Find out dataset id for an existing file

        :type sample_file_path: str
        :param sample_file_path: the local file path to the file
        :type galaxy_name: str
        :param galaxy_name: the full path to the sample file as it
        exists in Galaxy
        :rtype: Boolean
        :return: True for unique or the id of the existing dataset
        """
        self.logger.debug(
            "Getting dataset ID for existing file: " +
            galaxy_name)
        found = False
        size = os.path.getsize(sample_file_path)
        self.library = self.gi.libraries.get(self.library.id)
        datasets = self.library.get_datasets(name=galaxy_name)
        for dataset in datasets:
            # Galaxy sometimes appends a newline, see:
            # https://bitbucket.org/galaxy/galaxy-dist/src/
            # 7e4d21621ce12e13ebbdf9fd3259df58c3ef124c/lib/
            # galaxy/datatypes/data.py?at=stable#cl-673
            if dataset.file_size in (size, size + 1):
                found = dataset.id
                break

        return found

    def add_samples_if_nec(self, samples=[], hist_id=None):
        """
        Uploads a list of samples if they are not already present in Galaxy

        :type samples: list
        :param samples: the list of samples to upload
        :return: The number of single files uploaded
        """
        file_sum = 0
        hist = self.histories

        for sample in samples:
            self.logger.debug("sample name is" + sample.name)
            self.create_folder_if_nec(self.ILLUMINA_PATH + '/' + sample.name)

            added_to_galaxy = []

            for sample_item in sample.get_reads():
                sample_folder_path = self.ILLUMINA_PATH + '/' + sample.name
                if isinstance(sample_item, SamplePair):
                    # Processing for a SamplePair
                    forward = sample_item.forward
                    reverse = sample_item.reverse
                    pair_path = sample_folder_path + "/" + sample_item.name

                    self.create_folder_if_nec(pair_path)
                    added_to_galaxy = self._add_file(added_to_galaxy,
                                                     pair_path,
                                                     forward)

                    forward.library_dataset_id = added_to_galaxy[0]['id']

                    added_to_galaxy = self._add_file(added_to_galaxy,
                                                     pair_path,
                                                     reverse)

                    reverse.library_dataset_id = added_to_galaxy[0]['id']

                else:
                    # Processing for a SampleFile
                    added_to_galaxy = self._add_file(added_to_galaxy,
                                                     sample_folder_path,
                                                     sample_item)
                    sample_item.library_dataset_id = added_to_galaxy[0]['id']
                    file_sum += 1

        return file_sum

    def add_samples_to_history(
            self, samples=[], hist_id=None, make_paired_collection=True):
        """
        Adds samples to history in Galaxy

        :type samples: list
        :param samples: the list of samples to upload to history
        :return: The collection array of added samples
        """
        collection_array = []
        hist = self.histories

        for sample in samples:
            self.logger.debug("sample name is" + sample.name)

            added_to_galaxy = []

            for sample_item in sample.get_reads():
                sample_folder_path = self.ILLUMINA_PATH + '/' + sample.name
                if isinstance(sample_item, SamplePair):
                    # Processing for a SamplePair
                    datasets = dict()

                    pair_path = sample_folder_path + "/" + sample_item.name
                    collection_name = str(sample.name) + "__" + str(
                        sample_item.name)

                    # Add datasets to the current history
                    datasets['forward'] = hist.upload_dataset_from_library(
                        hist_id,
                        sample_item.forward.library_dataset_id
                    )['id']

                    datasets['reverse'] = hist.upload_dataset_from_library(
                        hist_id,
                        sample_item.reverse.library_dataset_id
                    )['id']

                    if make_paired_collection:
                        # Put datasets into the collection
                        collection_elem_ids = [{
                            "src": "hda",
                            "name": "forward",
                            "id": datasets['forward']
                        }, {
                            "src": "hda",
                            "name": "reverse",
                            "id": datasets['reverse']
                        }]
                        collection_array.append({
                            'src': 'new_collection',
                            'name': collection_name,
                            'collection_type': 'paired',
                            'element_identifiers': collection_elem_ids,
                        })

                        # Hide datasets in history
                        hist.update_dataset(
                            hist_id,
                            datasets['forward'],
                            visible=False
                        )
                        hist.update_dataset(
                            hist_id,
                            datasets['reverse'],
                            visible=False
                        )

                else:
                    # Processing for a SampleFile

                    hist.upload_dataset_from_library(
                        hist_id,
                        sample_item.library_dataset_id
                    )

        if collection_array != []:
            collection_title = 'IridaImport - ' + str(datetime.datetime.now())
            collection_desc = {
                "name": collection_title,
                "collection_type": "list:paired",
                "element_identifiers": collection_array
            }
            added_to_history = hist.create_dataset_collection(
                hist_id,
                collection_desc
            )

        return collection_array

    def _add_file(self, added_to_galaxy=None, sample_folder_path=None,
                  sample_file=None):
        """
        Upload a sample's sample files into Galaxy

        :type sample_folder_path: str
        :param sample_folder_path: A directory path for where the sample
        get_roles
        :type sample_file: SampleFile
        :param sample_file: A file object containing the file to upload
        :return: dataset object or the id of an existing dataset
        """
        galaxy_sample_file_name = sample_folder_path + '/' + sample_file.name
        if os.path.isfile(sample_file.path):
            if self.unique_file(sample_file.path, galaxy_sample_file_name):
                self.logger.debug(
                    "  Sample file does not exist so uploading/linking it")
                added = self.link(
                    sample_file, sample_folder_path)
                if(added):
                    added_to_galaxy = added
                    self.print_logged(time.strftime("[%D %H:%M:%S]:") +
                                      ' Imported file with Galaxy path: ' +
                                      galaxy_sample_file_name)
                    self.uploaded_files_log.append(
                        {'galaxy_name': galaxy_sample_file_name})
            else:
                # Return dataset id of existing file
                dataset_id = self.existing_file(sample_file.path,
                                                galaxy_sample_file_name)
                added_to_galaxy = [{'id': dataset_id}]
                self.print_logged(time.strftime("[%D %H:%M:%S]:") +
                                  ' Skipped file with Galaxy path: ' +
                                  galaxy_sample_file_name)
                self.skipped_files_log.append(
                    {'galaxy_name': galaxy_sample_file_name})
        else:
            error = ("File not found:\n Galaxy path:{0}\nLocal path:{1}"
                     ).format(galaxy_sample_file_name, sample_file.path)
            raise ValueError(error)

        return added_to_galaxy

    def link(self, sample_file, sample_folder_path):
        """
        Add a sample file to Galaxy, linking to it locally

        :type sample_file: SampleFile
        :param sample_file: the sample file to link
        :type sample_folder_path: str
        :param sample_folder_path: the folder in Galaxy to store the file in
        :return: a list containing a single dict with the file's
        url, id, and name.
        """
        self.logger.debug('      Attempting to upload a file')
        added = None
        file_path = sample_file.path
        self.logger.debug(
            "       Sample file's local path is" + file_path)
        file_type = 'auto'
        # Assume fastq files are fastqsanger:
        if os.path.splitext(file_path)[1] == '.fastq':
            file_type = 'fastqsanger'

        folder_id = self.reg_gi.libraries.get_folders(
            self.library.id, name=sample_folder_path)[0]['id']
        added = self.reg_gi.libraries.upload_from_galaxy_filesystem(
            self.library.id,
            file_path,
            folder_id=folder_id,
            link_data_only='link_to_files',
            file_type=file_type
        )

        return added

    def print_summary(self, failed=False):
        """
        Print a final summary of the tool's activity
        """
        def print_files_log(message, log):
            """For the summary, print a log's file's details"""
            if log:
                self.print_logged(message)
                for file_log in log:
                    self.print_logged('File with Galaxy path: {0}'
                                      .format(file_log['galaxy_name']))

        if failed:
            self.print_logged('Import failed.')
        else:
            self.print_logged('Import completed successfully.')
        self.print_logged('Final summary:\n'
                          '{0} file(s) imported and {1} file(s) skipped.'
                          .format(len(self.uploaded_files_log),
                                  len(self.skipped_files_log)))
        print_files_log(
            '\nSome files were skipped because they were not unique:',
            self.skipped_files_log)

    def print_logged(self, message):
        """Print a message and log it"""
        self.logger.info(message)
        print message

    def get_IRIDA_session(self, oauth_dict):
        """
        Create an OAuth2 session with IRIDA

        :type oauth_dict: dict
        :param oauth_dict: configuration information
        """
        redirect_uri = oauth_dict['redirect']
        auth_code = oauth_dict['code']
        if self.token:
            irida = OAuth2Session(client_id=self.CLIENT_ID,
                                  redirect_uri=redirect_uri,
                                  token={'access_token': self.token})
        else:
            irida = OAuth2Session(self.CLIENT_ID, redirect_uri=redirect_uri)
            irida.fetch_token(
                self.TOKEN_ENDPOINT, client_secret=self.CLIENT_SECRET,
                authorization_response=redirect_uri + '?code=' + auth_code)
        if PRINT_TOKEN_INSECURELY:
            self.print_logged(irida.token)
        return irida

    def configure(self):
        """
        Configure the tool using the configuration file

        """
        this_module_path = os.path.abspath(__file__)
        parent_folder = os.path.dirname(this_module_path)
        src = os.path.join(parent_folder, self.XML_FILE_SAMPLE)
        dest = os.path.join(parent_folder, self.XML_FILE)
        # Allows storing recommended configuration options in a sample XML file
        # and not commiting the XML file that Galaxy will read:
        try:
            shutil.copyfile(src, dest)
        except:
            pass

        config_path = os.path.join(parent_folder, self.CONFIG_FILE)
        with open(config_path, 'r') as config_file:
            config = ConfigParser.ConfigParser()
            config.readfp(config_file)

            # TODO: parse options from command line and config file as a list
            self.ADMIN_KEY = config.get('Galaxy', 'admin_key')
            self.GALAXY_URL = config.get('Galaxy', 'galaxy_url')
            self.ILLUMINA_PATH = config.get('Galaxy', 'illumina_path')
            self.REFERENCE_PATH = config.get('Galaxy', 'reference_path')
            self.XML_FILE = config.get('Galaxy', 'xml_file')

            self.TOKEN_ENDPOINT_SUFFIX = config.get('IRIDA',
                                                    'token_endpoint_suffix')
            self.INITIAL_ENDPOINT_SUFFIX = config.get('IRIDA',
                                                      'initial_endpoint_suffix')

            irida_loc = config.get('IRIDA', 'irida_url')
            self.TOKEN_ENDPOINT = irida_loc + self.TOKEN_ENDPOINT_SUFFIX
            irida_endpoint = irida_loc + self.INITIAL_ENDPOINT_SUFFIX

            self.CLIENT_ID = config.get('IRIDA', 'client_id')
            self.CLIENT_SECRET = config.get('IRIDA', 'client_secret')

            # Configure the tool XML file
            # The Galaxy server must be restarted for XML configuration
            # changes to take effect.
            # The XML file is only changed to reflect the IRIDA URL
            # and IRIDA client ID
            xml_path = os.path.join(parent_folder, self.XML_FILE)
            tree = ElementTree.parse(xml_path)

            inputs = tree.find('inputs')
            inputs.set('action', irida_endpoint)
            params = inputs.findall('param')
            client_id_param = next(param for param in params
                                   if param.get('name') == self.CLIENT_ID_PARAM)
            client_id_param.set('value', self.CLIENT_ID)

            tree.write(xml_path)

    def import_to_galaxy(self, json_parameter_file, log, hist_id, token=None,
                         config_file=None):
        """
        Import samples and their sample files into Galaxy from IRIDA

        :type json_parameter_file: str
        :param json_parameter_file: a path that Galaxy passes,
        to the stub datasource it created
        :type log: str
        :param log: the name of a file to write the tool's log to.
        :type token: str
        :param token: An access token that can be passed to the tool when it
        is manually run.
        :type config_file: str
        :param config_file: the name of a file to configure from
        """
        collection_array = []
        num_files = 0
        self.pp = pprint.PrettyPrinter(indent=4)

        self.logger.setLevel(logging.INFO)
        self.configure()
        with open(json_parameter_file, 'r') as param_file_handle:

            full_param_dict = json.loads(param_file_handle.read())
            param_dict = full_param_dict['param_dict']
            json_params_dict = json.loads(param_dict['json_params'])

            self.print_logged("Importing files from IRIDA to Galaxy...")

            self.uploaded_files_log = []
            self.skipped_files_log = []

            samples_dict = json_params_dict['_embedded']['samples']
            email = json_params_dict['_embedded']['user']['email']
            addtohistory = json_params_dict['_embedded']['addtohistory']
            desired_lib_name = json_params_dict['_embedded']['library']['name']
            oauth_dict = json_params_dict['_embedded']['oauth2']

            make_paired_collection = True

            if "makepairedcollection" in json_params_dict['_embedded']:
                make_paired_collection = json_params_dict['_embedded']['makepairedcollection']

            self.token = token
            self.irida = self.get_IRIDA_session(oauth_dict)

            self.gi = GalaxyInstance(self.GALAXY_URL, self.ADMIN_KEY)

            # This is necessary for uploads from arbitary local paths
            # that require setting the "link_to_files" flag:
            self.reg_gi = galaxy.GalaxyInstance(
                url=self.GALAXY_URL,
                key=self.ADMIN_KEY)

            self.histories = self.reg_gi.histories

            # Each sample contains a list of sample files
            samples = self.get_samples(samples_dict)

            # Set up the library
            self.library = self.get_first_or_make_lib(desired_lib_name, email)
            self.create_folder_if_nec(self.ILLUMINA_PATH)
            self.create_folder_if_nec(self.REFERENCE_PATH)

            # Add each sample's files to the library
            num_files = self.add_samples_if_nec(samples, hist_id)

            if addtohistory:
                if make_paired_collection:
                    collection_array = self.add_samples_to_history(samples, hist_id)
                    self.print_logged("Samples added to history!")
                    self.logger.debug("Collection items: \n" + self.pp.pformat(
                        collection_array))
                else:
                    collection_array = self.add_samples_to_history(
                        samples, hist_id, make_paired_collection=False)
                    self.print_logged("Samples added to history!")
            else:
                self.print_logged("Samples not added to history!")

            self.logger.debug("Number of files on galaxy: " + str(num_files))

            self.print_summary()

"""
From the command line, pass JSON files to IridaImport, and set up the logger
"""
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-p', '--json_parameter_file', dest='json_parameter_file',
        default='sample.dat',
        help='A JSON formatted parameter file from Galaxy.',
             metavar='json_parameter_file')
    parser.add_argument(
        '-l', '--log-file', dest='log', default='log_file',
        help="The file to which the tool will output the log.", metavar='log')
    parser.add_argument(
        '-t', '--token', dest='token',
        help='The tool can use a supplied access token instead of querying '
             + 'IRIDA.', metavar='token')
    parser.add_argument(
        '-c', '--config', action='store_true', default=False, dest='config',
        help='The tool must configure itself before Galaxy can be started. '
             + 'Use this option to do so. config.ini should be in the main '
             + 'irida_import folder.')
    parser.add_argument(
        '-i', '--history-id', dest='hist_id', default=False,
        help='The tool requires a History ID.')

    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    log_format = "%(levelname)s: %(message)s"
    logging.basicConfig(filename=args.log,
                        format=log_format,
                        level=logging.ERROR,
                        filemode="w")

    importer = IridaImport()
    logging.debug("Reading from passed file")

    if args.config:
        if os.path.isfile('config.ini'):
            importer.configure()
            message = 'Successfully configured the XML file!'
            logging.info(message)
            print message
        else:
            message = ('Error: Could not find config.ini in the irida_importer'
                       + ' directory!')
            logging.info(message)
            print message
    else:
        try:
            file_to_open = args.json_parameter_file
            importer.import_to_galaxy(file_to_open, args.log, args.hist_id,
                                      token=args.token)
        except Exception:
            logging.exception('')
            importer.print_summary(failed=True)
            raise
