import optparse
import logging
import sys
from bioblend.galaxy.objects import *
from bioblend import galaxy

import json
from sample import Sample
from sample_file import SampleFile


class IridaImport:

    """
    Imports sample's sample files from IRIDA.

    Appropriate folders are created
    """

    ADMIN_KEY = "09008eb345c9d5a166b0d8f301b1e72c"
    GALAXY_URL = "http://localhost:8888/"
    ILLUMINA_PATH = '/illumina_reads'
    REFERENCE_PATH = '/references'

    # TODO: choose/use a suitable library for interpreting IRIDA output json
    def get_samples(self, irida_info_dict):
        """
        Create sample objects from a dictionary.

        :type irida_info_dict: dict
        :param irida_info_dict: a dictionary to parse. See one of the test
        json files for formating information (the format will likely
        change soon)
        :return: list of output samples
        """
        samples = []
        for sample_input in irida_info_dict['_embedded']['samples']:
            sample_name = sample_input['sample_name']
            sample_path = sample_input['_links']['self']['href']

            sample = Sample(sample_name, sample_path)

            for sample_file_input in sample_input['_embedded']['sample_files']:
                sample_file_path = sample_file_input['_links']['self']['href']
                sample.sample_files.append(SampleFile(sample_file_path))

            samples.append(sample)
        return samples

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
            "If neccessary, making a folder named \"%s\" on base folder path"
            "\"%s\" from folder path \"%s\"" %
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
            elif base_folder_path == '/':
                made_folder = self.library.create_folder(folder_name)
            else:
                raise IOError('base_folder_path must include an existing base'
                              'folder, or nothing')
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

    def upload_sample_if_nec(self, sample):
        """
        Upload a sample's sample files if they are not already present in Galaxy

        :type sample: Sample
        :param sample: the sample to upload
        """
        for sample_file in sample.sample_files:
            sample_folder_path = self.ILLUMINA_PATH+'/'+sample.name
            galaxy_sample_file_name = sample_folder_path+'/'+sample_file.name
            logging.debug(
                "Doing a basic check for already existing sample file at: " +
                galaxy_sample_file_name)
            logging.debug(
                "Sample name:" +
                sample.name +
                " Sample file name:" +
                sample_file.name)
            if not self.exists_in_lib('file', 'name', galaxy_sample_file_name):
                logging.debug(
                    "  Sample file does not exist so uploading/linking it")
                self.upload_or_link(sample_file, sample_folder_path)
            else:
                logging.debug("  Sample file already exists!")

    # TODO: use urllib.request.URLopener (right now only local files work)
    def upload_or_link(self, sample_file, sample_folder_path):
        """
        Upload a sample file to Galaxy, linking to it locally if possible.

        :type sample_file: SampleFile
        :param sample_file: the sample file to upload
        :type sample_folder_path: str
        :param sample_folder_path: the URI to get the file from

        """
        logging.debug('      Attempting to upload or link a file')

        # Get the 'file' 'http' prefix from the
        # 'file://...'  or 'http://..' path
        prefix = sample_file.path.split(':/')[0]
        logging.debug(
            "       Sample file's path's prefix is \"%s\" and path is \"%s\"" %
            (prefix, sample_file.path))
        if prefix == 'file':

            # Get e.g. '/folder/folder56/myfile.fastq' from
            # 'file://folder/folder56/myfile.fastq'
            file_path = "/" + sample_file.path.split('/', 3)[3]
            logging.debug("File path is"+file_path)

            folder_id = self.reg_gi.libraries.get_folders(
                self.library.id,
                name=sample_folder_path)[0]['id']

            self.reg_gi.libraries.upload_from_galaxy_filesystem(
                self.library.id,
                file_path,
                folder_id=folder_id,
                link_data_only='link_to_files')

    # TODO: finish this method
    def assign_ownership_if_nec(self, sample):
        """
        Assign ownership to the files in a sample, if neccessary

        :type sample: Sample
        :param sample: the sample who's sample files will be assigned ownership
        """
        return True  # neccessary here

    def import_to_galaxy(self, json_parameter_file, irida_info):
        """
        Import samples and their sample files into Galaxy from IRIDA

        :type json_parameter_file: str
        :param json_parameter_file: the JSON string that Galaxy passes,
        describing the stub datasource it created
        :type irida_info: str
        :param irida_info: the JSON string passed by IRIDA, describing
        the samples to upload
        """
        irida_info_dict = json.loads(irida_info)

        user_email = irida_info_dict['user_email']
        desired_lib_name = irida_info_dict['library_name']

        self.gi = GalaxyInstance(self.GALAXY_URL, self.ADMIN_KEY)

        # This is necessary for uploads from arbitary local paths
        # that require setting the "link_to_files" flag:
        self.reg_gi = galaxy.GalaxyInstance(
            url=self.GALAXY_URL,
            key=self.ADMIN_KEY)

        # Each sample contains a list of sample files
        samples = self.get_samples(irida_info_dict)
        # Set up the library
        self.library = self.get_first_or_make_lib(desired_lib_name)
        self.create_folder_if_nec(self.ILLUMINA_PATH)
        self.create_folder_if_nec(self.REFERENCE_PATH)

        # Add each sample's files to the library
        for sample in samples:
            logging.debug("sample name is" + sample.name)
            self.create_folder_if_nec(self.ILLUMINA_PATH+'/'+sample.name)
            self.upload_sample_if_nec(sample)
            self.assign_ownership_if_nec(sample)

        return True  # for the first unit test

"""
From the command line, pass json files to IridaImport, and set up the logger
"""
if __name__ == '__main__':
    logging.basicConfig(filename="log_irida_import", level=logging.DEBUG,
                        filemode="w")
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    logger = logging.getLogger()
    logger.addHandler(stream_handler)

    logging.debug("Parsing the Command Line")
    parser = optparse.OptionParser()
    parser.add_option(
        '-p', '--json_parameter_file', dest='json_parameter_file',
        action='store', type="string", default=None,
        help='json_parameter_file')
    parser.add_option(
        '-s', '--irida_info', dest='irida_info',
        action='store', type="string", default=None,
        help='irida_info')
    (options, args) = parser.parse_args()

    logging.debug("Opening a test json file")
    test_json_file = open(
        '/home/jthiessen/galaxy-dist/tools/irida_import/prelim_json.json')
    test_json = test_json_file.read()

    importer = IridaImport()
    importer.import_to_galaxy(options.json_parameter_file, test_json)
