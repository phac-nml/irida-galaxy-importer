"""
This file is responsible for managing the execution of an IRIDA instance and Test Suites
"""
import unittest
from os import path

from irida_import.tests.integration.irida_data_setup import SetupIridaData
from irida_import.tests.integration.galaxy_data_setup import SetupGalaxyData
from irida_import.tests.integration.test_irida_importer import IridaImporterTestSuite

# Modules level variables that can/will be changed when the setup starts
irida_base_url = "http://localhost:8080/api/"
username = "jeff"
password = "password1"
client_id = "myClient"
client_secret = "myClientSecret"

galaxy_url = None

# Deal with 'AF_UNIX path too long' errors
repo_path = path.join('/tmp', 'repos')


def init_irida_setup(branch, db_host, db_port):
    """
    Initializes the Irida setup object
    :param branch: what branch from github to check out
    :param db_host: database host override
    :param db_port: database port override
    :return: SetupIridaData object
    """
    global irida_base_url
    global username
    global password
    global client_id
    global client_secret

    return SetupIridaData(irida_base_url[:irida_base_url.index("/api")], username, password, branch, db_host, db_port, repo_dir=repo_path)


def init_galaxy_setup():
    """
    Initializes the Galaxy setup object
    :return:
    """
    return SetupGalaxyData(repo_dir=repo_path)


def create_test_suite():
    """
    Finds all the integration tests and adds them to a test suite
    :return: unittest.TestSuite
    """
    suite = unittest.TestSuite()

    # Include all the classes that contain tests
    test_class_list = [IridaImporterTestSuite]

    # for each class, find the tests and add them to the test suite
    for test_class in test_class_list:
        for class_method in [*test_class.__dict__]:
            if class_method.startswith("test_"):
                suite.addTest(test_class(class_method))

    return suite


def start(irida_branch="master", db_host="localhost", db_port="3306"):
    """
    Start running the integration tests

    This is the entry point for the integration tests
    :param irida_branch: what branch from github to check out
    :param db_host: database host override
    :param db_port: database port override
    :return:
    """
    exit_code = 0

    # create a handler to manage a headless IRIDA instance
    irida_handler = init_irida_setup(irida_branch, db_host, db_port)

    # Create handler for Galaxy
    galaxy_handler = init_galaxy_setup()
    global galaxy_url
    galaxy_url = galaxy_handler.GALAXY_URL

    try:
        # Install IRIDA packages
        irida_handler.install_irida()
        # Delete and recreate the database
        irida_handler.reset_irida_db()
        # Launch IRIDA
        # Note: This initializes the database tables
        # Note: This call waits until IRIDA is running
        irida_handler.run_irida()
        # Add data to database that the tests depend on
        irida_handler.update_irida_db()

        # install an instance of galaxy
        galaxy_handler.install_galaxy()
        # setup data for galaxy
        galaxy_handler.setup_galaxy()
        # start galaxy
        galaxy_handler.start_galaxy()

        # configure galaxy post startup
        galaxy_handler.register_galaxy()
        galaxy_handler.configure_galaxy_api_key()
        galaxy_handler.configure_tool('Galaxy', 'galaxy_url', galaxy_url)

        # Run tests
        full_suite = create_test_suite()

        runner = unittest.TextTestRunner()
        res = runner.run(full_suite)
        if not res.wasSuccessful():
            exit_code = 1
    except Exception as e:
        raise e
    finally:
        # Make sure IRIDA and Galaxy are stopped even when an exception is raised
        irida_handler.stop_irida()
        galaxy_handler.stop_galaxy()

    return exit_code
