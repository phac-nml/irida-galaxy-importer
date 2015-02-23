import pytest
import json
import logging
from ...irida_import import IridaImport
from ...sample import Sample
from bioblend.galaxy.objects import GalaxyInstance
from bioblend.galaxy.objects import Library
from bioblend.galaxy.objects import Folder
from bioblend.galaxy.objects import client
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
        """Create a JSON string representative of the Galaxy dataset file"""
        logging.debug("Making a test json file")
        test_json_dict = {
            "param_dict": {
                "library_name": "boblib",
                "userId": "1",
                "dbkey": "?",
                "sample1_name": "thisissample1'sname",
                "__user__": "galaxy.model:User",
                "__app__": "galaxy.app:UniverseApplication",
                "sample1_path": "http://localhost/some_IRIDA_API_path/Projects/1/Samples/1",
                "__user_name__": "jthiessen",
                "runtool_btn": "Execute",
                "__user_id__": "1",
                "sample1_file2_path": "file://localhost/home/jthiessen/lib_imp_dir/test/test.fastq",
                "__root_dir__": "/home/jthiessen/galaxy-dist",
                "sample1_file1_path": "http://www.dgfdg.com/sample1file1"}}
        return json.dumps(test_json_dict)

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
        samples = imp.get_samples(param_dict)
        assert isinstance(samples, list), 'A list must be returned'
        for sample in samples:
            assert isinstance(sample, Sample), 'The list must contain samples'
            assert len(samples) == 1, 'Number of samples is incorrect'

    def test_get_first_or_make_lib_empty(self, imp):
        """Test library creation if there are no preexisting libraries"""
        wanted_name = 'boblib'
        lib_to_make = mock.create_autospec(Library)
        lib_to_make.name = wanted_name
        lib_to_make.deleted = False
        imp.gi.libraries.create = Mock(return_value=lib_to_make)
        imp.gi.libraries.list = Mock(return_value=[lib_to_make])

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

    def test_create_folder_if_nec_base(self, imp):
        """Create a folder, as if its base folder exists"""

        base_folder = mock.create_autospec(Folder)
        folder_name = 'sample1'
        folder_path = '/illumina_reads/'+folder_name
        folder = mock.create_autospec(Folder)
        folder.name = folder_path

        picked_f_id = 1234567
        imp.reg_gi.libraries.get_folders = Mock(
            return_value=[{'id': picked_f_id}])
        imp.library = self.make_lib('wolib', False)
        imp.library.id = 123
        imp.library.get_folder = Mock(return_value=base_folder)
        imp.library.create_folder = Mock(return_value=folder)

        # IridaImport.exists_in_lib(...) is tested elsewhere
        imp.exists_in_lib = Mock(return_value=False)

        made_folder = imp.create_folder_if_nec(folder_path)

        assert (imp.reg_gi.libraries.get_folders.call_count is 1,
                'Base folders should only be looked for once')
        assert (imp.library.get_folder.call_count is 1,
                'Only one base folder should be obtained')

        # Can't add assertion message here--either inside the method, or
        # by wrapping with an assert
        imp.library.get_folder.assert_called_with(picked_f_id)

        assert (imp.library.create_folder.call_count is 1,
                'Only 1 folder must be created')
        assert (made_folder.name == folder_path,
                'The created folder must have the correct name')

    # TODO: finish this method
    def test_create_folder_if_nec_no_base(self, imp):
        with pytest.raises(IOError):
            """Correctly raise an exception if the base folder doesn't exist"""
            raise IOError
            return True
