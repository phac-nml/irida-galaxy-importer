import pytest
import json
import logging
from sample import Sample
from bioblend.galaxy.objects import *
from mock import Mock
import mock


class TestIridaImport:

    @pytest.fixture(scope='class')
    def setup_logging(self):
        logging.basicConfig(filename="log_irida_import",
                            level=logging.DEBUG, filemode="w")

    @pytest.fixture(scope="class")
    def setup_json(self):
        logging.debug("Opening a test json file")
        test_json_file = open('prelim_json.json')
        test_json = test_json_file.read()
        return test_json

    @pytest.fixture(scope="class")
    def imp(self):
        import irida_import
        return irida_import.IridaImport()

    def test_get_samples(self, imp, setup_json):
        irida_info_dict = json.loads(setup_json)
        samples = imp.get_samples(irida_info_dict)
        size = len(irida_info_dict['_embedded']['samples'])

        assert isinstance(samples, list), 'A list must be returned'
        for sample in samples:
            assert isinstance(sample, Sample), 'The list must contain samples'
        assert len(samples) == size, 'Number of samples is incorrect'

    def test_get_first_or_make_lib(self, imp):
        wanted_name = 'boblib'

        lib_to_make = mock.create_autospec(Library)
        lib_to_make.name = Mock()
        lib_to_make.name = wanted_name
        lib_to_make.deleted = Mock()
        lib_to_make.deleted = False

        imp.gi = Mock()
        imp.gi.libraries = Mock()

        imp.gi.libraries.create = Mock(return_value=lib_to_make)
        imp.gi.libraries.list = Mock(return_value=[lib_to_make])

        lib_made = imp.get_first_or_make_lib(wanted_name)

        assert lib_made is not None
        assert lib_made.name == wanted_name
        assert lib_made.deleted is False

    # Right now, adds sample files and folders to Galaxy, without any assertions
    def test_import_to_galaxy_integration(self, imp, setup_json):
        assert(imp.import_to_galaxy("", setup_json))
        return True
