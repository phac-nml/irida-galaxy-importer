import logging
import sys
from bioblend.galaxy.objects import GalaxyInstance
from bioblend import galaxy
import json
from sample import Sample
from sample_file import SampleFile
import optparse
import os.path
from requests_oauthlib import OAuth2Session

# FOR DEVELOPMENT ONLY!!
# This value only exists for this process and processes that fork from it (none)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


class IridaImport:

    """
    Imports sample's sample files from IRIDA.

    Appropriate folders are created
    """

    ADMIN_KEY = "09008eb345c9d5a166b0d8f301b1e72c"
    GALAXY_URL = "http://localhost:8888/"
    ILLUMINA_PATH = '/illumina_reads'
    REFERENCE_PATH = '/references'

    CLIENT_ID = 'webClient'
    CLIENT_SECRET = 'webClientSecret'

    TOKEN_ENDPOINT = 'http://localhost:8080/api/oauth/token'

    def get_samples(self, samples_dict):
        """
        Create sample objects from a dictionary.

        :type json_params_dict: dict
        :param json_params__dict: a dictionary to parse. See one of the test
        json files for formating information (the format will likely
        change soon)
        :return: a list of output samples
        """
        samples = []
        for sample_input in samples_dict:
            sample_name = sample_input['name']
            sample_path = sample_input['_links']['self']['href']

            sample = Sample(sample_name, sample_path)

            for sample_file_input in sample_input['_embedded']['sample_files']:
                sample_file_url = sample_file_input['_links']['self']['href']

                sample_file = self.get_sample_file(sample_file_url)
                sample.sample_files.append(sample_file)

            samples.append(sample)
        return samples

    def get_sample_file(self, sample_file_url):
        """
        From an IRIDA REST API URL, get a sample file
        :type str
        :param sample_file_url: the URL to get the sample file representation
        :return: a sample file with a name and path
        """
        response = self.irida.get(sample_file_url)
        resource = response.json()['resource']
        name = resource['fileName']
        path = resource['file']
        return SampleFile(name, path)

    def get_user_lib(self, user_email, desired_lib_name):
        """
        If possible, get a library that the user has permissions for

       :type user_email: str
       :param user_email: the Galaxy username to attempt to make the
       library for
       :type desired_lib_name: str
       :param desired_lib_name: the name
       """

        return True

    def get_first_or_make_lib(self, desired_lib_name):
        """"
        Get or if neccessary create a library that matches a given name.

        :type desired_lib_name: str
        :param desired_lib_name: the desired library name
        :rtype: :class:`~.LibraryDataset`
        :return: the obtained or created library
        """
        lib = None
        libs = self.gi.libraries.list(name=desired_lib_name)
        if len(libs) > 0:
            lib = next(lib_i for lib_i in libs if lib_i.deleted is False)

        if(lib is None):
            lib = self.gi.libraries.create(desired_lib_name)
        return lib

    def create_folder_if_nec(self, folder_path):
        """
        Add a folder to a library, if it does not already exist.

        :type folder_path: str
        :param folder_patht: The folder's path e.g. '/bobfolder/bobfolder2'
        """
        made_folder = None
        # Get the folder name from the path, e.g. 'bobfolder2' from
        # '/bobfolder/bobfolder2'
        folder_name = folder_path.rsplit("/", 1)[1]
        # Get the base folder path from the path e.g '/bobfolder' from
        # '/bobfolder/bobfolder2'
        base_folder_path = folder_path.rsplit("/", 1)[0]
        logging.debug(
            'If neccessary, making a folder named \'%s\' on base folder path'
            '\'%s\' from folder path \'%s\'' %
            (folder_name, base_folder_path, folder_path))

        if not self.exists_in_lib('folder', 'name', folder_path):

            base_folder_list = self.reg_gi.libraries.get_folders(
                self.library.id,
                name=base_folder_path)

            if len(base_folder_list) > 0:
                base_folder = self.library.get_folder(base_folder_list[0]['id'])
                made_folder = self.library.create_folder(
                    folder_name,
                    base_folder=base_folder)
            elif base_folder_path == '':
                made_folder = self.library.create_folder(folder_name)
            else:
                raise IOError('base_folder_path must include an existing base'
                              'folder, or nothing')
            logging.debug('Made folder with path:' + '\'%s\'' % folder_path)
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
        # check for an object of the desired type with the desired attribute
        for con_inf in self.library.content_infos:
            if con_inf.type == item_type:
                attr = getattr(con_inf, item_attr_name)
                if attr == desired_attr_value:
                    ans = True
                    break
        return ans

    def add_sample_if_nec(self, sample):
        """
        Upload a sample's sample files if they are not already present in Galaxy

        :type sample: Sample
        :param sample: the sample to upload
        """
        added_to_galaxy = []
        for sample_file in sample.sample_files:
            sample_folder_path = self.ILLUMINA_PATH+'/'+sample.name
            galaxy_sample_file_name = sample_folder_path+'/'+sample_file.name
            logging.debug(
                "Doing a basic check for already existing sample file at: " +
                galaxy_sample_file_name)
            logging.debug(
                " Sample name:" +
                sample.name +
                " Sample file name:" +
                sample_file.name)
            if not self.exists_in_lib('file', 'name', galaxy_sample_file_name):
                logging.debug(
                    "  Sample file does not exist so uploading/linking it")
                added = self.link_or_download(sample_file, sample_folder_path)
                if(added):
                    added_to_galaxy.extend(added)
            else:
                logging.debug("  Sample file already exists!")
        return added_to_galaxy

    # TODO: use urllib.request.URLopener (right now only local files work)
    def link_or_download(self, sample_file, sample_folder_path):
        """
        Add a sample file to Galaxy, linking to it locally if possible.

        :type sample_file: SampleFile
        :param sample_file: the sample file to download
        :type sample_folder_path: str
        :param sample_folder_path: the folder in Galaxy to store the file in
        :return: a list containing a single dict with the file's
        url, id, and name.
        """
        logging.debug('      Attempting to upload or link a file')
        added = None
        file_path = sample_file.path
        logging.debug(
            "       Sample file's full path  is" + file_path)

        folder_id = self.reg_gi.libraries.get_folders(
            self.library.id,
            name=sample_folder_path)[0]['id']

        if os.path.isfile(file_path):
            added = self.reg_gi.libraries.upload_from_galaxy_filesystem(
                self.library.id,
                file_path,
                folder_id=folder_id,
                link_data_only='link_to_files')
            logging.debug('wrote file!')
        else:
            raise IOError('file not found: '+file_path)
        return added

    def assign_ownership_if_nec(self, sample):
        """
        Assign ownership to the files in a sample, if neccessary

        :type sample: Sample
        :param sample: the sample whose sample files will be assigned ownership
        """
        # TODO: finish this method
        return True  # neccessary here

    def get_IRIDA_session(self, oauth_dict):
        """
        Create an OAuth2 session with IRIDA

        :type oauth_dict dict
        :param oauth_dict: configuration information
        """
        redirect_uri = oauth_dict['redirect']
        auth_code = oauth_dict['code']

        irida = OAuth2Session(self.CLIENT_ID, redirect_uri=redirect_uri)
        irida.fetch_token(
            self.TOKEN_ENDPOINT, client_secret=self.CLIENT_SECRET,
            authorization_response=redirect_uri + '?code=' + auth_code)
        return irida

    def import_to_galaxy(self, json_parameter_file, irida_info):
        """
        Import samples and their sample files into Galaxy from IRIDA

        :type json_parameter_file: str
        :param json_parameter_file: a path that Galaxy passes,
        to the stub datasource it created
        :type irida_info: str
        :param irida_info: a local JSON file containing configuration info.
        It is currently unused, and may be depreciated.
        """
        with open(json_parameter_file, 'r') as param_file_handle:
            full_param_dict = json.loads(param_file_handle.read())
            param_dict = full_param_dict['param_dict']
            json_params_dict = json.loads(param_dict['json_params'])

            logging.debug("The full Galaxy param dict is: " +
                          json.dumps(full_param_dict, indent=2))
            logging.debug("The JSON parameters from IRIDA are:\n" +
                          json.dumps(json_params_dict, indent=2))

            samples_dict = json_params_dict['_embedded']['samples']
            email = json_params_dict['_embedded']['user']['email']
            desired_lib_name = json_params_dict['_embedded']['library']['name']
            oauth_dict = json_params_dict['_embedded']['oauth2']

            self.irida = self.get_IRIDA_session(oauth_dict)

            self.gi = GalaxyInstance(self.GALAXY_URL, self.ADMIN_KEY)

            # This is necessary for uploads from arbitary local paths
            # that require setting the "link_to_files" flag:
            self.reg_gi = galaxy.GalaxyInstance(
                url=self.GALAXY_URL,
                key=self.ADMIN_KEY)

            # Each sample contains a list of sample files
            samples = self.get_samples(samples_dict)

            # Set up the library
            self.library = self.get_first_or_make_lib(desired_lib_name)
            self.create_folder_if_nec(self.ILLUMINA_PATH)
            self.create_folder_if_nec(self.REFERENCE_PATH)

            # Add each sample's files to the library
            for sample in samples:
                logging.debug("sample name is" + sample.name)
                self.create_folder_if_nec(self.ILLUMINA_PATH+'/'+sample.name)
                self.add_sample_if_nec(sample)
                self.assign_ownership_if_nec(sample)


"""
From the command line, pass json files to IridaImport, and set up the logger
"""
if __name__ == '__main__':
    # TODO: convert to robustly use argparse
    logging.basicConfig(filename="log_irida_import", level=logging.DEBUG,
                        filemode="w")
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    logger = logging.getLogger()
    logger.addHandler(stream_handler)

    # Prevent urllib3 from spamming stdout
    urllib3_logger = logging.getLogger('requests.packages.urllib3')
    urllib3_logger.setLevel(logging.WARNING)

    logging.debug("Parsing the Command Line")
    parser = optparse.OptionParser()
    parser.add_option(
        '-p', '--json_parameter_file', dest='json_parameter_file',
        action='store', type="string", default=None,
        help='json_parameter_file')
    parser.add_option(
        '-s', '--irida_info', dest='irida_info',
        action='store', type="string", default=None,
        help='configuration file will go here')
    (options, args) = parser.parse_args()

    # this test JSON file does not have to be configured to run the tests
    logging.debug("Opening a test json file")
    test_json_file = \
        '/home/jthiessen/galaxy-dist/tools/irida_import_tool_for_galaxy/irida_import/sample.dat'

    importer = IridaImport()

    if options.irida_info is None:
        logging.debug("No passed file so reading local file")
        importer.import_to_galaxy(test_json_file, None)
    else:
        logging.debug("Reading from passed file")
        importer.import_to_galaxy(options.json_parameter_file, None)
