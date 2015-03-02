import pytest
import json
import logging
from ...irida_import import IridaImport
from ...sample import Sample
from ...sample_file import SampleFile
from bioblend.galaxy.objects import GalaxyInstance
from bioblend.galaxy.objects import Library
from bioblend.galaxy.objects import Folder
from bioblend.galaxy.objects import client
from bioblend.galaxy.objects.wrappers import LibraryContentInfo
from bioblend import galaxy
from mock import Mock
import mock


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
        # py.test messes up the paths to modules and packages
        # I haven't found a way to get around it without hardcoding paths
        test_json_file = open(test_path)
        test_json = test_json_file.read()
        return test_json

    @pytest.fixture(scope="function")
    def imp(self):
        """Create an IridaImport instance to test"""
        imp = IridaImport()
        imp.gi = mock.create_autospec(GalaxyInstance)
        imp.gi.libraries = mock.create_autospec(client.ObjLibraryClient)
        imp.reg_gi = mock.create_autospec(galaxy.GalaxyInstance)
        imp.reg_gi.libraries = mock.create_autospec(galaxy.libraries)
        return imp

    def test_get_samples(self, imp, setup_json):
        """
        Test if correct samples are read from the json string

        The tested method is expected to change soon.
        """
        param_dict = json.loads(setup_json)['param_dict']
        json_params = json.loads(param_dict['json_params'])
        samples = imp.get_samples(json_params)
        assert isinstance(
            samples, list), 'A list must be returned'
        for sample in samples:
            assert isinstance(sample, Sample), 'The list must contain samples'
        assert len(samples) == 3, 'Number of samples is incorrect'

    def test_get_first_or_make_lib_empty(self, imp):
        """Test library creation if there are no preexisting libraries"""
        wanted_name = 'boblib'
        lib_to_make = mock.create_autospec(Library)
        lib_to_make.name = wanted_name
        lib_to_make.deleted = False
        imp.gi.libraries.create = Mock(return_value=lib_to_make)
        imp.gi.libraries.list = Mock(return_value=[])

        lib_made = imp.get_first_or_make_lib(wanted_name)

        assert (imp.gi.libraries.create.call_count == 1,
                'Only 1 library must be created')
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

        lib_made = imp.get_first_or_make_lib(wanted_name)

        assert (imp.gi.libraries.create.call_count is 1,
                'Only 1 library must be created')
        assert lib_made is not None, 'library must be returned'
        assert lib_made.name == wanted_name, 'Library must have correct name'
        assert lib_made.deleted is False, 'Library must not be deleted'

    def make_lib(self, name, is_deleted):
        """Set up a library to be used by a test"""
        lib_to_make = mock.create_autospec(Library)
        lib_to_make.name = name
        lib_to_make.deleted = is_deleted
        return lib_to_make

    def test_create_folder_if_nec_base(
            self,
            imp):
        """Create a folder, as if its base folder exists"""

        base_folder = mock.create_autospec(
            Folder)
        folder_name = 'sample1'
        folder_path = '/illumina_reads/' + folder_name
        folder = mock.create_autospec(Folder)
        folder.name = folder_path

        picked_f_id = 1234567
        imp.reg_gi.libraries.get_folders = Mock(
            return_value=[{'id': picked_f_id}])
        imp.library = self.make_lib('wolib', False)
        imp.library.id = 123
        imp.library.get_folder = Mock(return_value=base_folder)
        imp.library.create_folder = Mock(return_value=folder)

        # IridaImport.exists_in_lib(...) is tested
        # elsewhere
        imp.exists_in_lib = Mock(
            return_value=False)

        made_folder = imp.create_folder_if_nec(
            folder_path)

        assert (imp.reg_gi.libraries.get_folders.call_count is 1,
                'Base folders should only be looked for once')
        assert (imp.library.get_folder.call_count is 1,
                'Only one base folder should be obtained')

        # Can't add assertion message here--either inside the method, or
        # by wrapping with an assert
        imp.library.get_folder.assert_called_with(
            picked_f_id)

        assert (imp.library.create_folder.call_count is 1,
                'Only 1 folder must be created')
        assert (made_folder.name == folder_path,
                'The created folder must have the correct name')

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
        items = []
        items.append(
            self.make_content_info('file', 'name', 'sally.fastq'))
        items.append(
            self.make_content_info('folder', 'name', 'bob.fasta'))
        items.append(
            self.make_content_info('file', 'name', 'bob.fasta'))
        imp.library.content_infos = items
        exists = imp.exists_in_lib('file', 'name', 'bob.fasta')
        assert exists, 'file must exist in library'

    def make_content_info(self, item_type, item_attr_name, item_attr_value):
        """ Make a content info object for a mock library """
        content_info = mock.create_autospec(LibraryContentInfo)
        content_info.type = item_type
        setattr(content_info, item_attr_name, item_attr_value)
        return content_info

    def test_upload_sample_if_nec(self, imp):
        """ Test if a new sample file is uploaded to the library """
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
        imp.exists_in_lib = Mock(return_value=False)
        imp.upload_or_link = Mock(return_value=file_list)

        sampleFile1 = SampleFile(
            "/imaginary/path/file1.fasta")
        sampleFile2 = SampleFile(
            "/imaginary/path/file2.fasta")
        sample = Sample(
            "bobname",
            "/imaginary/path/Samples/1")
        sample.sample_files.append(sampleFile1)
        sample.sample_files.append(sampleFile2)

        uploaded = imp.upload_sample_if_nec(sample)
        assert uploaded, 'files must be uploaded'
        assert (imp.upload_or_link.call_count is 2,
                'The 2 files should be uploaded once each')
        assert uploaded == file_list, "The correct files must be uploaded"
