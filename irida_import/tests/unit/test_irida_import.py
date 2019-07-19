import ast
import os
import json
import logging
import pprint
import pytest
import mock

from requests_oauthlib import OAuth2Session
from mock import Mock
from bioblend import galaxy
from bioblend.galaxy.objects import (GalaxyInstance, Library, Folder, client)
from bioblend.galaxy.objects.wrappers import LibraryContentInfo
from ...irida_import import IridaImport
from ...sample import Sample
from ...sample_file import SampleFile
from ...sample_pair import SamplePair


class TestIridaImport:

    """ TestIridaImport performs unit tests on IridaImport."""

    @pytest.fixture(scope='class')
    def setup_logging(self):
        """Create and configure a logging object"""
        logging.basicConfig(filename="log_irida_import",
                            level=logging.DEBUG, filemode="w")

    @pytest.fixture(scope="class")
    def setup_json(self):
        """Create a json string from a text file"""
        logging.debug("Opening a test json string")
        test_path = 'tests/unit/data/test.dat'
        # Pytest messes up the paths to modules and packages.
        # I haven't found a way to get around it without hardcoding paths.
        # Reading a file is neccessary to avoid writing large PEP8 commpliant
        # dicts or JSON strings.
        test_json_file = open(test_path)
        test_json = test_json_file.read()
        return test_json

    @pytest.fixture(scope="function")
    def imp(self):
        """Create an IridaImport instance to test"""
        imp = IridaImport()
        imp.irida = mock.create_autospec(OAuth2Session)
        imp.gi = mock.create_autospec(GalaxyInstance)
        imp.gi.libraries = mock.create_autospec(client.ObjLibraryClient)
        imp.gi.histories = mock.create_autospec(client.ObjHistoryClient)
        imp.reg_gi = mock.create_autospec(galaxy.GalaxyInstance)
        imp.reg_gi.datasets = mock.create_autospec(galaxy.datasets.DatasetClient)
        imp.reg_gi.libraries = mock.create_autospec(galaxy.libraries.LibraryClient)
        imp.reg_gi.libraries.get_folders.return_value = [{'id': '321'}, {}]
        imp.library = mock.create_autospec(galaxy.objects.wrappers.Library)
        imp.library.id = "123"
        imp.reg_gi.histories = mock.create_autospec(galaxy.histories.HistoryClient)
        imp.histories = mock.create_autospec(galaxy.histories.HistoryClient)
        imp.reg_gi.users = mock.create_autospec(galaxy.users)
        imp.reg_gi.roles = mock.create_autospec(galaxy.roles)
        imp.uploaded_files_log = []
        imp.pp = pprint.PrettyPrinter(indent=4)
        imp.skipped_files_log = []
        imp.configure = Mock()
        imp.logger = logging.getLogger('irida_import')
        self.add_irida_constants(imp)
        return imp

    def add_irida_constants(self, irida_instance):
        """Add constants to a passed IRIDA instance"""
        irida_instance.ADMIN_KEY = "09008eb345c9d5a166b0d8f301b1e72c"
        irida_instance.GALAXY_URL = "http://localhost:8888/"
        irida_instance.ILLUMINA_PATH = '/illumina_reads'
        irida_instance.REFERENCE_PATH = '/references'
        irida_instance.MAX_WAITS = 1
        irida_instance.MAX_CLIENT_ATTEMPTS = 10
        irida_instance.CLIENT_RETRY_DELAY = 30
        irida_instance.CLIENT_ID = 'webClient'
        irida_instance.CLIENT_SECRET = 'webClientSecret'
        irida_instance.TOKEN_ENDPOINT = 'http://localhost:8080/api/oauth/token'

    @pytest.fixture(scope='class')
    def file_list(self):
        """Obtain a list of files as if read from Galaxy"""
        file_list = [
            {
                'url': '/api/libraries/lala/contents/lala1',
                'id': '59606d2a36c77a56',
                'name': 'file1.fasta'
            },
            {
                'url': '/api/libraries/lala/contents/lala2',
                'id': '59606d2a36c77a57',
                'name': 'file2.fasta'
            }
        ]
        return file_list

    @pytest.fixture(scope='class')
    def folder_list(self):
        """Obtain a list of folders as if read from Galaxy"""
        # TODO: doublecheck this dict is correct
        folder_list = [
            {
                'url': '/api/libraries/lala/contents/lala2',
                'id': '59606d2a36c77a56',
                'name': '/bobfolder1'
            },
            {
                'url': '/api/libraries/lala/contents/lala1',
                'id': '59606d2a36c77a57',
                'name': '/bobfolder/bobfolder2'
            },
            {
                'url': '/api/libraries/lala/contents/lala3',
                'id': '59606d2a36c77a58',
                'name': '/bobfolder1/bobfolder2/bobfolder3'
            }
        ]
        return folder_list

    def test_get_samples(self, imp, setup_json):
        """
        Test if correct samples are read from the json string

        The tested method is expected to change soon.
        """
        param_dict = json.loads(setup_json)['param_dict']
        json_params = json.loads(param_dict['json_params'])
        sample_file = SampleFile('nameish', 'pathish')
        imp.get_sample_file = Mock(return_value=sample_file)

        samples = imp.get_samples(json_params['_embedded']['samples'])

        assert isinstance(
            samples, list), 'A list must be returned'
        for sample in samples:
            assert isinstance(sample, Sample), 'The list must contain samples'
        assert len(samples) == 1, 'Number of samples is incorrect'

    def test_get_first_or_make_lib_empty(self, imp):
        """Test library creation if there are no preexisting libraries"""
        wanted_name = 'boblib'
        lib_to_make = mock.create_autospec(Library)
        lib_to_make.name = wanted_name
        lib_to_make.deleted = False
        lib_to_make.id = 1
        imp.gi.libraries.create = Mock(return_value=lib_to_make)
        imp.gi.libraries.list = Mock(return_value=[])
        email = 'bob@lala.com'
        users = [self.make_role('sally@lala.com', 59),
                 self.make_role(email, 34)]
        imp.reg_gi.roles.get_roles = Mock(return_value=users)

        imp.reg_gi.libraries.set_library_permissions = Mock()

        lib_made = imp.get_first_or_make_lib(wanted_name, email)

        assert imp.gi.libraries.create.call_count == 1, \
            'Only 1 library must be created'
        assert lib_made is not None, 'library must be returned'
        assert lib_made.name == wanted_name, 'Library must have correct name'
        assert lib_made.deleted is False, 'Library must not be deleted'

    def test_get_first_or_make_lib_preexisting(self, imp):
        """Test library creation given preexisting libraries"""
        wanted_name = 'boblib'
        lib_to_make = self.make_lib(wanted_name, False)
        chaff_lib = self.make_lib('boblib', True)
        chaff_lib2 = self.make_lib('boblib2', False)
        libs_in_gal = [lib_to_make, chaff_lib, chaff_lib2]
        imp.gi.libraries.list = Mock(return_value=libs_in_gal)
        imp.gi.libraries.create = Mock(return_value=lib_to_make)
        email = 'bob@lala.com'
        users = [self.make_role('sally@lala.com', 59),
                 self.make_role(email, 34)]
        imp.reg_gi.roles.get_roles = Mock(return_value=users)

        lib_made = imp.get_first_or_make_lib(wanted_name, email)

        assert imp.gi.libraries.create.call_count == 0, \
            'No library must be created'
        assert lib_made is not None, 'library must be returned'
        assert lib_made.name == wanted_name, 'Library must have correct name'
        assert lib_made.deleted is False, 'Library must not be deleted'

    def make_lib(self, name, is_deleted):
        """Set up a library to be used by a test"""
        lib_to_make = mock.create_autospec(Library)
        lib_to_make.name = name
        lib_to_make.deleted = is_deleted
        lib_to_make.id = 1
        return lib_to_make

    def make_role(self, email, id):
        role = {'name': email, 'id': id}
        return role

    def test_create_folder_if_nec_base(self, imp):
        """Create a folder, as if its base folder exists"""
        base_folder = mock.create_autospec(
            Folder)
        folder_name = 'sample1'
        folder_path = '/illumina_reads/' + folder_name
        folder = mock.create_autospec(Folder)
        folder.name = folder_path
        folder_id = 123

        picked_f_id = 1234567

        # IridaImport.exists_in_lib(...) is tested
        # elsewhere
        imp.exists_in_lib = Mock()
        imp.exists_in_lib.side_effect = [False, [picked_f_id]]

        imp.library = Mock(return_value=[2222])

        imp.reg_gi.libraries.create_folder = Mock(
            return_value=[{'id': 123 , 'type':'folder', 'name':'/illumina_reads/sample1'}])


        made_folder_id = imp.create_folder_if_nec(
            folder_path)

        assert made_folder_id == folder_id, \
            'The created folder has id'

    def test_create_folder_if_nec_wrong_base(self, imp):
        with pytest.raises(IOError):
            """Raise an exception if the folder's  base folder doesn't exist"""

            folder_name = 'sample1'
            folder_path = '/illumina_reads/' + folder_name
            folder = mock.create_autospec(Folder)
            folder.name = folder_path

            imp.reg_gi.libraries.get_folders = Mock(return_value=[])
            imp.library = self.make_lib('wolib', False)
            imp.library.id = 123

            imp.exists_in_lib = Mock(return_value=False)
            imp.create_folder_if_nec(folder_path)

    def test_exists_in_lib(self, imp):
        """ Test if a folder can be found in a library among chaff items """
        imp.library = self.make_lib('wolib', False)
        imp.gi.libraries.get = Mock(return_value=imp.library)


        items = {}
        items['sally.fastq']={}
        items['sally.fastq']['id']=123
        items['sally.fastq']['type']='file'
        items['sally.fastq']['name']='sally.fastq'

        items['bob.fasta']={}
        items['bob.fasta']['id']=234
        items['bob.fasta']['type']='file'
        items['bob.fasta']['name']='bob.fasta'

        imp.folds = items

        exists = imp.exists_in_lib('file', 'name', 'bob.fasta')
        assert exists, 'file must exist in library'

    def test_add_samples_if_nec(self, imp, file_list):
        """ Test if a new sample file is added to the library """

        imp.exists_in_lib = Mock()
        imp.exists_in_lib.side_effect = [[123], [234]]

        imp.link = mock.create_autospec(IridaImport.link)
        imp._add_file = mock.create_autospec(IridaImport._add_file)
        imp._add_file.return_value = [{'id': '321'}]
        side_effect_list = [[file_dict] for file_dict in file_list]
        imp.link.side_effect = side_effect_list
        os.path.isfile = Mock(return_value=True)
        imp.unique_file = Mock(return_value=True)

        sampleFile1 = SampleFile('file1', "/imaginary/path/file1.fasta")
        sampleFile2 = SampleFile('file2', "/imaginary/path/file2.fasta")
        samplePair1 = SamplePair(
            'pair1',
            sampleFile1,
            sampleFile2
        )

        num_files = 4
        sample = Sample("bobname",
                        "/imaginary/path/Samples/1/paired",
                        "/imaginary/path/Samples/1/unpaired")
        sample.add_file(sampleFile1)
        sample.add_file(sampleFile2)
        sample.add_pair(samplePair1)

        samples = [sample]

        num_added = imp.add_samples_if_nec(samples)

        assert num_added, 'a file must be added'
        assert imp._add_file.call_count is num_files, \
            'The %s files should be uploaded once each' % num_files

        assert num_added == 4, "The correct amount of files need to be uploaded"

    def test_add_samples_to_history(self, imp, file_list):
        """ Test if a new sample file is added to the library """
        imp.exists_in_lib = Mock(return_value=False)
        imp.link = mock.create_autospec(IridaImport.link)
        imp._add_file = mock.create_autospec(IridaImport._add_file)
        imp._add_file.return_value = [{'id': '321'}]
        side_effect_list = [[file_dict] for file_dict in file_list]
        imp.link.side_effect = side_effect_list
        os.path.isfile = Mock(return_value=True)
        os.path.getsize = Mock(return_value=5678)
        imp.unique_file = Mock(return_value=True)

        history = imp.reg_gi.histories.create_history()

        sampleFile1 = SampleFile('file1', "/imaginary/path/file1.fasta")
        sampleFile2 = SampleFile('file2', "/imaginary/path/file2.fasta")
        samplePair1 = SamplePair(
            'pair1',
            sampleFile1,
            sampleFile2
        )

        num_pairs = 1
        sample = Sample("bobname",
                        "/imaginary/path/Samples/1/paired",
                        "/imaginary/path/Samples/1/unpaired")
        sample.add_file(sampleFile1)
        sample.add_file(sampleFile2)
        sample.add_pair(samplePair1)

        samples = [sample]

        collection_array = imp.add_samples_to_history(samples, history['id'])

        assert collection_array, 'a pair must be added'
        assert collection_array[0]['collection_type'] is 'paired' and len(
            collection_array) is num_pairs, ('The %s pair should be uploaded'
                                             + 'once') % num_pairs

        collection_array = []

        collection_array = imp.add_samples_to_history(samples, history['id'],
                                                      make_paired_collection=False)

        assert not collection_array, 'List should be empty, collections was set to false'

    def test_link(self, imp, folder_list):
        """Test uploading a local sample file to Galaxy as a link"""
        imp.library = mock.create_autospec(Library)
        imp.library.id = 12345
        imp.reg_gi.libraries.get_folders = Mock(return_value=folder_list)
        single_file_list = [
            {
                'url': '/api/libraries/lala/contents/lala1',
                'id': '59606d2a36c77a56',
                'name': 'file1.fasta'
            }
        ]
        imp.reg_gi.libraries.upload_from_galaxy_filesystem = Mock(
            return_value=single_file_list)

        sample_file = SampleFile('file1', 'file:///imaginary/path/file1.fasta')
        sample_folder_path = '/bobfolder1/bobfolder2/bobfolder3'
        uploaded = imp.link(sample_file, sample_folder_path)
        assert uploaded == single_file_list, 'The correct file must be made'

    def test_assign_ownership_if_nec(self, imp):
        # TODO: write the functionality for this to test
        return True

    def test_import_to_galaxy(self, setup_json, mocker):
        """Test reading a file and running apropriate methods"""
        mocker.patch('bioblend.galaxy.objects.GalaxyInstance', autospec=True)
        mocked_open_function = mock.mock_open(read_data=setup_json)
        with mock.patch("__builtin__.open", mocked_open_function):
            imp = IridaImport()
            imp.reg_gi = mock.create_autospec(galaxy.GalaxyInstance)
            imp.reg_gi.histories = mock.create_autospec(galaxy.histories.HistoryClient)
            imp.histories = None
            lib = mock.create_autospec(Library)
            imp.get_first_or_make_lib = Mock(return_value=lib)
            imp.create_folder_if_nec = Mock()
            imp.add_samples_if_nec = mock.create_autospec(IridaImport.add_samples_if_nec)
            imp.samples_uploaded_successfully = mock.create_autospec(IridaImport.samples_uploaded_successfully)
            imp.add_samples_to_history = (
                mock.create_autospec(IridaImport.add_samples_to_history))
            imp.assign_ownership_if_nec = Mock()
            imp.get_IRIDA_session = Mock()
            imp.get_sample_file = Mock()
            imp.get_sample_meta = Mock()
            imp.get_samples = Mock()
            imp.configure = Mock()
            imp.MAX_RETRIES = 3
            imp.make_irida_request = Mock()
            self.add_irida_constants(imp)

            # Create a history first
            history = imp.reg_gi.histories.create_history()

            # Config data to come
            imp.import_to_galaxy("any_string", None, history['id'])

            assert isinstance(imp.gi, type(GalaxyInstance)), \
                   'A GalaxyInstance must be created'
            assert imp.get_first_or_make_lib.call_count == 1, \
                'One library should be created'
            assert imp.create_folder_if_nec.call_count >= 2, \
                'At least the illumina and reference folders must be made'
