from __future__ import absolute_import

import datetime
import json
import logging
import os.path
import pprint
import re
import sys
import time

from bioblend import galaxy
from bioblend.galaxy.objects import GalaxyInstance
from requests_oauthlib import OAuth2Session

from irida_import.sample import Sample
from irida_import.sample_file import SampleFile
from irida_import.sample_pair import SamplePair

from irida_import.irida_file_storage_azure import IridaFileStorageAzure
#from irida_import.irida_file_storage_aws import IridaFileStorageAws as iridaFileStorage
#from irida_import.irida_file_storage_local import IridaFileStorageLocal as iridaFileStorage

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

    folds = {}

    uploaded_files_log = []
    skipped_files_log = []

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger('irida_import')
        self.iridaFileStorage = IridaFileStorageAzure(config)

    def initial_lib_state(self):

        if not self.folds:
            library_info = self.reg_gi.libraries.show_library(self.library.id,contents=True)
            for lib_item in library_info:
                name = lib_item['name']
                self.folds[name]={}
                self.folds[name]['id']=lib_item['id']
                self.folds[name]['type']=lib_item['type']
                self.folds[name]['name']=name

        return True

    def get_samples(self, samples_dict, include_assemblies):
        """
        Gets sample objects from a dictionary.

        :type samples_dict: dict
        :param samples_dict: a dictionary to parse. See one of the test
        json files for formatting information (the format will likely
        change soon)
        :type include_assemblies: boolean
        :param include_assemblies: A boolean whether or not to include assemblies with the import
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
                sample.add_file(self.get_sample_file(single['sequenceFile']))

            if include_assemblies:
                assembly_resource = self.make_irida_request(sample.assembly_path)
                for assembly in assembly_resource['resources']:
                    sample.add_file(self.get_sample_file(assembly))

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
            assembly_path = ""

            for link in paths:
                if link['rel'] == "sample/sequenceFiles/pairs":
                    paired_path = link['href']
                elif link['rel'] == "sample/sequenceFiles/unpaired":
                    unpaired_path = link['href']
                elif link['rel'] == "sample/assemblies":
                    assembly_path = link['href']

            samples.append(Sample(sample_name, paired_path, unpaired_path, assembly_path))
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
        final_id=None
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

        exist_id = self.exists_in_lib('folder', 'name', folder_path)

        if not exist_id:

            base_folder_id = self.exists_in_lib('folder', 'name', base_folder_path)
            ans = []
            name = ''

            if base_folder_id:
                ans = self.reg_gi.libraries.create_folder(self.library.id,folder_name,base_folder_id=base_folder_id[0])
                name = base_folder_path + "/" + ans[0]['name']
            elif base_folder_path == '':
                ans = self.reg_gi.libraries.create_folder(self.library.id,folder_name)
                name = "/" + ans[0]['name']
            else:
                raise IOError('base_folder_path must include an existing base '
                              + 'folder, or nothing')

            #add to the current state of the library
            self.folds[name]={}
            self.folds[name]['id']=ans[0]['id']
            self.folds[name]['type']='folder'
            self.folds[name]['name']=name
            final_id=ans[0]['id']

            self.logger.debug(
                'Made folder with path:' + '\'%s\'' % folder_path)
        else:
            #to ensure consistent results, always pick first entry
            #we have no other way of knowing which one to use.
            final_id=exist_id[0]


        return final_id

    def exists_in_lib(self, item_type, item_attr_name, desired_attr_value):
        """
        Find if an item of given type and attribute exists in the library

        :type item_type: str
        :param item_type: the item type e.g "folder" or "file"
        :type item_attr_name: str
        :param item_attr_name: the item attribute e.g "name"
        :type desired_attr_value: str
        :param desired_attr_value: the desired attribute value e.g "Bob"

        :rtype: List of Ids or Empty list
        :return: Return item unique IDs or empty list if item(s) does not exist in the library
        """
        ans = []

        # check cache before fetching from galaxy.
        # current state of the library should only change between irida_import.py invocation
        if not self.folds:
            self.initial_lib_state()

        for item_name in self.folds:
            if item_type == self.folds[item_name]['type']:
                if desired_attr_value == self.folds[item_name][item_attr_name]:
                    ans.append(self.folds[item_name]['id'])

        return ans



    def existing_file(self, sample_file_path, galaxy_name):
        """
        Find out dataset id for an existing file

        :type sample_file_path: str
        :param sample_file_path: the local file path to the file
        :type galaxy_name: str
        :param galaxy_name: the full path to the sample file as it
        exists in Galaxy
        :rtype: Boolean
        :return: Return file unique ID otherwise Boolean False
        """
        self.logger.debug(
            "Getting dataset ID for existing file: " +
            galaxy_name)
        found = False
        size = iridaFileStorage.getFileSize(sample_file_path)

        # check cache before fetching from galaxy.
        # current state of the library should only change between irida_import.py invocation
        if not self.folds:
            self.initial_lib_state()

        #found all datasets with the galaxy_name
        #first attempt will assume there is only one which is not right
        datasets = self.exists_in_lib('file', 'name', galaxy_name)

        if datasets:
            for data_id in datasets:
                item = self.reg_gi.libraries.show_dataset(self.library.id,data_id)
                if item['file_size'] in (size, size + 1) and item['state'] == 'ok':
                    found = item['id']
                    break

        return found

    def verify_sample_integrity(self, sample_file):
        """
        Checks to see if a sample was uploaded successfully

        :type sample: SampleFile
        :param samples: the sample to verify upload
        :return: boolean indicating whether the sample was uploaded successfully
        """
        sample_integrity_verified = sample_file.verified

        if not sample_integrity_verified:
            self.logger.debug(time.strftime("[%D %H:%M:%S]:") +
                              ' Verifying integrity of: ' +
                              sample_file.name)
            num_waits = 0
            while num_waits <= self.config.MAX_WAITS:
                state = sample_file.state(self.reg_gi, self.library.id)
                if state == 'ok': # uploaded succesfully
                    self.logger.debug(time.strftime("[%D %H:%M:%S]:") + ' OK! ')
                    sample_integrity_verified = True
                    sample_file.verified = True
                    break
                elif state in ['new', 'upload', 'queued', 'running', 'setting_metadata']: # pending
                    self.logger.debug(time.strftime("[%D %H:%M:%S]:") + ' PENDING! (%s)' % (state))
                    num_waits += 1
                    time.sleep(5)
                else:
                    self.logger.debug(time.strftime("[%D %H:%M:%S]:") + ' NOT OK! ')
                    # delete the dataset from the library
                    retries = 0
                    while retries <= self.MAX_RETRIES:
                        if sample_file.delete(self.reg_gi, self.library.id):
                            sample_file.library_dataset_id = None
                            break
                    break

        return sample_integrity_verified

    def samples_uploaded_successfully(self, samples=[]):
        """
        Checks to see if all of our samples were uploaded successfully

        :type samples: list
        :param samples: the list of samples to verify upload
        :return: boolean indicating whether all of the samples were uploaded successfully
        """
        samples_uploaded_successfully = True

        # Check that samples have been added
        for sample in samples:
            for sample_item in sample.get_reads():
                if isinstance(sample_item, SamplePair):
                    forward_result = self.verify_sample_integrity(sample_item.forward)
                    reverse_result = self.verify_sample_integrity(sample_item.reverse)
                    if not forward_result or not reverse_result:
                        samples_uploaded_successfully = False
                else:
                    sample_result = self.verify_sample_integrity(sample_item)
                    if not sample_result:
                        samples_uploaded_successfully = False

        return samples_uploaded_successfully

    def add_samples_if_nec(self, samples=[]):
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
            sample_root_folder_id = self.create_folder_if_nec(self.config.ILLUMINA_PATH + '/' + sample.name)

            added_to_galaxy = []

            for sample_item in sample.get_reads():
                sample_folder_path = self.config.ILLUMINA_PATH + '/' + sample.name
                if isinstance(sample_item, SamplePair):
                    # Processing for a SamplePair
                    forward = sample_item.forward
                    reverse = sample_item.reverse
                    pair_path = sample_folder_path + "/" + sample_item.name

                    #since doing pair, will not be writting to the 'main' folder for the sample
                    sample_folder_id = self.create_folder_if_nec(pair_path)

                    added_to_galaxy = self._add_file(added_to_galaxy,
                                                     pair_path,sample_folder_id,
                                                     forward)

                    file_sum += 1

                    added_to_galaxy = self._add_file(added_to_galaxy,
                                                     pair_path,sample_folder_id,
                                                     reverse)

                    file_sum += 1

                else:
                    # Processing for a SampleFile
                    added_to_galaxy = self._add_file(added_to_galaxy,
                                                     sample_folder_path,sample_root_folder_id,
                                                     sample_item)
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
        collection_name_count = {}
        hist = self.histories
        for sample in samples:
            self.logger.debug("sample name is" + sample.name)

            added_to_galaxy = []

            for sample_item in sample.get_reads():
                sample_folder_path = self.config.ILLUMINA_PATH + '/' + sample.name
                if isinstance(sample_item, SamplePair):
                    # Processing for a SamplePair
                    datasets = dict()

                    pair_path = sample_folder_path + "/" + sample_item.name

                    if sample.name in collection_name_count:
                        collection_name = str(sample.name) + "__" + str(collection_name_count[sample.name])
                        collection_name_count[sample.name] += 1
                    else:
                        collection_name = str(sample.name)
                        collection_name_count[sample.name] = 2

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

    def _add_file(self, added_to_galaxy=None, sample_folder_path=None,sample_folder_id=None,
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
        if iridaFileStorage.fileExists(sample_file.path):
            if sample_file.library_dataset_id == None:
                #grab dataset_id if it does exist, if not will be given False
                dataset_id = self.existing_file(sample_file.path,galaxy_sample_file_name)

                if dataset_id:
                    # Return dataset id of existing file
                    added_to_galaxy = [{'id': dataset_id}]
                    self.print_logged(time.strftime("[%D %H:%M:%S]:") +
                                      ' Skipped file with Galaxy path: ' +
                                      galaxy_sample_file_name)
                    sample_file.verified = True
                    self.skipped_files_log.append(
                        {'galaxy_name': galaxy_sample_file_name})
                else:
                    self.logger.debug(
                        "  Sample file does not exist so uploading/linking it")
                    added = self.link(
                        sample_file, sample_folder_id)
                    if(added):
                        added_to_galaxy = added
                        self.print_logged(time.strftime("[%D %H:%M:%S]:") +
                                          ' Imported file with Galaxy path: ' +
                                          galaxy_sample_file_name)
                        self.uploaded_files_log.append(
                            {'galaxy_name': galaxy_sample_file_name})

                sample_file.library_dataset_id = added_to_galaxy[0]['id']

        else:
            error = ("File not found:\n Galaxy path:{0}\nLocal path:{1}"
                     ).format(galaxy_sample_file_name, sample_file.path)
            raise ValueError(error)

        return added_to_galaxy

    def link(self, sample_file, folder_id):
        """
        Add a sample file to Galaxy, linking to it locally

        :type sample_file: SampleFile
        :param sample_file: the sample file to link
        :type folder_id: ID of folder to link file to
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
        print(message)

    def get_IRIDA_session(self, oauth_dict):
        """
        Create an OAuth2 session with IRIDA

        :type oauth_dict: dict
        :param oauth_dict: configuration information
        """
        redirect_uri = oauth_dict['redirect']
        auth_code = oauth_dict['code']
        if self.token:
            irida = OAuth2Session(client_id=self.config.CLIENT_ID,
                                  redirect_uri=redirect_uri,
                                  token={'access_token': self.token})
        else:
            irida = OAuth2Session(self.config.CLIENT_ID, redirect_uri=redirect_uri)
            irida.fetch_token(
                self.config.TOKEN_ENDPOINT, client_secret=self.config.CLIENT_SECRET,
                authorization_response=redirect_uri + '?code=' + auth_code)
        if PRINT_TOKEN_INSECURELY:
            self.print_logged(irida.token)
        return irida



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
            if "includeAssemblies" in json_params_dict['_embedded']:
                include_assemblies = json_params_dict['_embedded']['includeAssemblies']
            else:
                include_assemblies = False
            desired_lib_name = json_params_dict['_embedded']['library']['name']
            oauth_dict = json_params_dict['_embedded']['oauth2']

            make_paired_collection = True

            if "makepairedcollection" in json_params_dict['_embedded']:
                make_paired_collection = json_params_dict['_embedded']['makepairedcollection']

            self.token = token
            self.irida = self.get_IRIDA_session(oauth_dict)

            self.gi = GalaxyInstance(self.config.GALAXY_URL, self.config.ADMIN_KEY)
            self.gi.gi.max_get_attempts = self.config.MAX_CLIENT_ATTEMPTS
            self.gi.gi.get_retry_delay = self.config.CLIENT_RETRY_DELAY


            # This is necessary for uploads from arbitary local paths
            # that require setting the "link_to_files" flag:
            self.reg_gi = galaxy.GalaxyInstance(
                url=self.config.GALAXY_URL,
                key=self.config.ADMIN_KEY)
            self.reg_gi.max_get_attempts = self.config.MAX_CLIENT_ATTEMPTS
            self.reg_gi.get_retry_delay = self.config.CLIENT_RETRY_DELAY

            self.histories = self.reg_gi.histories

            # Each sample contains a list of sample files
            samples = self.get_samples(samples_dict, include_assemblies)

            # Set up the library
            self.library = self.get_first_or_make_lib(desired_lib_name, email)
            self.create_folder_if_nec(self.config.ILLUMINA_PATH)
            self.create_folder_if_nec(self.config.REFERENCE_PATH)

            # Add each sample's files to the library
            retries = 0
            while (retries <= self.config.MAX_RETRIES):
                num_files = self.add_samples_if_nec(samples)

                self.logger.debug(time.strftime("[%D %H:%M:%S]:") + ' Checking if Samples uploaded successfully! ')
                if self.samples_uploaded_successfully(samples):
                    break
                else:
                    retries += 1

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
