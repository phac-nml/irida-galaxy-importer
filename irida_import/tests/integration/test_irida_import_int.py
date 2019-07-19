import socket
import getpass
import inspect
import time
import sys
import logging
import os
import ConfigParser
import pytest
import subprocess32
from tempfile import mkdtemp
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotVisibleException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ...irida_import import IridaImport
from . import util
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import LegacyApplicationClient
from bioblend import galaxy

# These variables are to stop Galaxy and Irida from being changed
# during script execution. This is required if you are using your
# own instance of Galaxy and Irida.
# os.environ['IRIDA_GALAXY_TOOL_TESTS_DONT_INSTALL'] = "1"
# os.environ['IRIDA_GALAXY_TOOL_TESTS_DONT_START_GALAXY'] = "1"
# os.environ['IRIDA_GALAXY_TOOL_TESTS_DONT_STOP_GALAXY'] = "1"
# os.environ['IRIDA_GALAXY_TOOL_TESTS_DONT_START_IRIDA'] = "1"


class TestIridaImportInt:
    """
    Perform integration tests on the IRIDA import tool for Galaxy

    To use an already running instance of Galaxy on port 8888, installation
    must be disabled, in addition to Galaxy starting/stopping
    """

    TIMEOUT = 600  # seconds
    GALAXY_SLEEP_TIME=360

    USER = getpass.getuser()
    EMAIL = 'irida@irida.ca'

    GALAXY_PASSWORD = 'Password1'
    GALAXY_DOMAIN = 'localhost'
    GALAXY_CMD = ['bash', 'run.sh', '--daemon']
    GALAXY_STOP = ['bash', 'run.sh', '--stop-daemon']
    GALAXY_DB_RESET = 'echo "drop database if exists galaxy_test; create database galaxy_test;" | psql'

    IRIDA_DOMAIN = 'localhost'
    IRIDA_PORT = 8080
    IRIDA_URL = 'http://' + IRIDA_DOMAIN + ':' + str(IRIDA_PORT)
    IRIDA_CMD = ['mvn', 'clean', 'jetty:run',
                 '-Djdbc.url=jdbc:mysql://localhost:3306/irida_test',
                 '-Djdbc.username=test', '-Djdbc.password=test',
                 '-Dliquibase.update.database.schema=true',
                 '-Dhibernate.hbm2ddl.auto=',
                 '-Dhibernate.hbm2ddl.import_files=']
    IRIDA_STOP = 'mvn jetty:stop'
    IRIDA_DB_RESET = 'echo '\
        '"drop database if exists irida_test;'\
        'create database irida_test;'\
        '"| mysql -u test -ptest'
    IRIDA_PASSWORD_ID = 'password_client'
    IRIDA_AUTH_CODE_ID = 'auth_code_client'
    IRIDA_USER = 'admin'
    IRIDA_PASSWORD = 'Password1!'
    IRIDA_TOKEN_ENDPOINT = IRIDA_URL + '/api/oauth/token'
    IRIDA_PROJECTS = IRIDA_URL + '/api/projects'

    IRIDA_GALAXY_MODAL = 'galaxy-modal'
    WAIT = 120

    INSTALL_EXEC = 'install.sh'

    # Sequence files accessed by IRIDA's REST API will not exist when the
    # tool attempts to access them if they were not uploaded as valid sequence
    # files
    FASTQ_CONTENTS = (
        "@SRR566546.970 HWUSI-EAS1673_11067_FC7070M:4:1:2299:1109 length=50\n" +
        "TTGCCTGCCTATCATTTTAGTGCCTGTGAGGTGGAGATGTGAGGATCAGT\n" +
        "+SRR566546.970 HWUSI-EAS1673_11067_FC7070M:4:1:2299:1109 length=50\n" +
        "hhhhhhhhhhghhghhhhhfhhhhhfffffe`ee[`X]b[d[ed`[Y[^Y")

    def setup_class(self):
        """Initialize class variables, install IRIDA, Galaxy, and the tool"""
        module_dir = os.path.dirname(os.path.abspath(__file__))
        self.SCRIPTS = os.path.join(module_dir, 'bash_scripts')
        self.REPOS_PARENT = module_dir
        self.REPOS = os.path.join(module_dir, 'repos')
        self.TOOL_DIRECTORY = os.path.dirname(inspect.getfile(IridaImport))
        self.CONFIG_PATH = os.path.join(self.TOOL_DIRECTORY, 'tests',
                                        'integration', 'repos', 'galaxy',
                                        'tools', 'irida_import', 'config.ini')

        self.GALAXY = os.path.join(self.REPOS, 'galaxy')
        self.IRIDA = os.path.join(self.REPOS, 'irida')

        log = logging.getLogger()
        log.setLevel(logging.DEBUG)
        log_out = logging.StreamHandler(sys.stdout)
        log_out.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        log_out.setFormatter(formatter)
        log.addHandler(log_out)
        self.log = log

        try:
            os.environ['IRIDA_GALAXY_TOOL_TESTS_DONT_INSTALL']
            self.GALAXY_PORT = 8080
            self.GALAXY_URL = 'http://' + self.GALAXY_DOMAIN + ':' + str(
                self.GALAXY_PORT)
        except KeyError:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('', 0))
            self.GALAXY_PORT = sock.getsockname()[1]
            self.GALAXY_URL = 'http://' + self.GALAXY_DOMAIN + ':' + str(
                self.GALAXY_PORT)

            # Install IRIDA, Galaxy, and the IRIDA export tool:
            exec_path = os.path.join(self.SCRIPTS, self.INSTALL_EXEC)
            install = subprocess32.Popen([exec_path, self.TOOL_DIRECTORY,
                                         str(self.GALAXY_PORT)],
                                         cwd=self.REPOS_PARENT)
            install.wait()  # Block untill installed

    @pytest.fixture(scope='class')
    def driver(self, request):
        """Set up the Selenium WebDriver"""
        driver = webdriver.Chrome()
        driver.implicitly_wait(1)
        driver.set_window_size(1024, 768)

        def finalize_driver():
            driver.quit()
        request.addfinalizer(finalize_driver)
        return driver

    @pytest.fixture(scope='class')
    def setup_irida(self, request, driver):
        """Set up IRIDA for tests (Start if required, register, log in)"""
        def stop_irida():
            print('Stopping IRIDA nicely')
            stopper = subprocess32.Popen(self.IRIDA_STOP, cwd=self.IRIDA,
                                         shell=True)
            stopper.wait()

        try:
            os.environ['IRIDA_GALAXY_TOOL_TESTS_DONT_START_IRIDA']
        except KeyError:
            stop_irida()

            # create temporary directories for IRIDA data
            data_dir = mkdtemp(prefix='irida-tmp-')
            sequence_file_dir = mkdtemp(prefix='sequence-files-',dir=data_dir)
            reference_file_dir = mkdtemp(prefix='reference-files-',dir=data_dir)
            output_file_dir = mkdtemp(prefix='output-files-',dir=data_dir)
            self.IRIDA_CMD.append('-Dsequence.file.base.directory='+sequence_file_dir)
            self.IRIDA_CMD.append('-Dreference.file.base.directory='+reference_file_dir)
            self.IRIDA_CMD.append('-Doutput.file.base.directory='+output_file_dir)

            subprocess32.call(self.IRIDA_DB_RESET, shell=True)
            subprocess32.Popen(self.IRIDA_CMD, cwd=self.IRIDA, env=os.environ)
            util.wait_until_up(self.IRIDA_DOMAIN, self.IRIDA_PORT,
                               self.TIMEOUT)

            def finalize_irida():
                stop_irida()
            request.addfinalizer(finalize_irida)
        self.register_irida(driver)
        self.add_irida_client_password(driver)
        self.add_irida_client_auth_code(driver)
        self.configure_irida_client_secret(driver)

        # Return an OAuth 2.0 authorized session with IRIDA
        return self.get_irida_oauth(driver)

    @pytest.fixture(scope='class')
    def setup_galaxy(self, request, driver):
        """Set up Galaxy for tests (Start if required, register, log in)"""
        def stop_galaxy():
            try:
                os.environ['IRIDA_GALAXY_TOOL_TESTS_DONT_STOP_GALAXY']
            except KeyError:
                print('Killing Galaxy')
                subprocess32.Popen(self.GALAXY_STOP, cwd=self.GALAXY)

        try:
            os.environ['IRIDA_GALAXY_TOOL_TESTS_DONT_START_GALAXY']
        except KeyError:
            stop_galaxy()
            subprocess32.call(self.GALAXY_DB_RESET, shell=True)
            subprocess32.Popen(self.GALAXY_CMD, cwd=self.GALAXY)
            self.log.debug("Waiting for Galaxy database migration [%s]. Sleeping for [%s] seconds",self.GALAXY_URL,self.GALAXY_SLEEP_TIME)
            time.sleep(self.GALAXY_SLEEP_TIME)
            self.log.debug("Galaxy database migration should have (hopefully) finished, checking if it is up")
            util.wait_until_up(
                self.GALAXY_DOMAIN,
                self.GALAXY_PORT,
                self.TIMEOUT)
            self.log.debug("Galaxy should now be up on [%s]",self.GALAXY_URL)

            def finalize_galaxy():
                stop_galaxy()
            request.addfinalizer(finalize_galaxy)
        self.register_galaxy(driver)
        self.configure_galaxy_api_key(driver)
        self.configure_tool('Galaxy', 'galaxy_url', self.GALAXY_URL)

    def test_galaxy_configured(self, setup_galaxy, driver):
        """Verify that Galaxy is accessible"""
        driver.get(self.GALAXY_URL)

    def test_irida_configured(self, setup_irida, driver):
        """Verify that IRIDA is accessible"""
        driver.get(self.IRIDA_URL)

    def test_tool_visible(self, setup_galaxy, driver):
        """Make sure there is a link to the tool in Galaxy"""
        driver.get(self.GALAXY_URL)
        driver.find_element_by_css_selector("#title_getext > a > span").click()
        assert(driver.find_element_by_link_text("IRIDA server"))

    def register_galaxy(self, driver):
        """Register with Galaxy, and then attempt to log in"""
        driver.get(self.GALAXY_URL)
        driver.find_element_by_link_text("Login or Register").click()
        driver.find_element_by_id("register-toggle").click()
        driver.find_element_by_name("email").send_keys(self.EMAIL)
        driver.find_element_by_name("password").send_keys("Password1")
        driver.find_element_by_name("confirm").send_keys(
            "Password1")
        driver.find_element_by_name("username").send_keys("irida-test")
        driver.find_element_by_name("create").click()

        try:
            driver.get(self.GALAXY_URL)
            driver.find_element_by_link_text("Login or Register").click()
            driver.find_element_by_name("login").send_keys(self.EMAIL)
            driver.find_element_by_name("password").send_keys("Password1")
            driver.find_element_by_name("login").click()
        except NoSuchElementException:
            pass

    def configure_galaxy_api_key(self, driver):
        """Make a new Galaxy admin API key and configure the tool to use it"""
        gal = galaxy.GalaxyInstance(self.GALAXY_URL,
                                    email=self.EMAIL,
                                    password=self.GALAXY_PASSWORD)
        self.configure_tool('Galaxy', 'admin_key', gal.key)
        print('key:' + gal.key)

    def configure_tool(self, section, option, value):
        """Write tool configuration data"""
        config = ConfigParser.ConfigParser()
        config.read(self.CONFIG_PATH)
        config.set(section, option, value)
        with open(self.CONFIG_PATH, 'w') as config_file:
            config.write(config_file)

    def register_irida(self, driver):
        """Register with IRIDA if neccessary, and then log in"""
        driver.get(self.IRIDA_URL)
        self.login_irida(driver, 'admin', 'password1')

        # Set a new password if necessary
        try:
            driver.find_element_by_id(
                "password").send_keys(self.IRIDA_PASSWORD)
            driver.find_element_by_id(
                "confirmPassword").send_keys(self.IRIDA_PASSWORD)
            driver.find_element_by_xpath("//button[@type='submit']").click()
        except NoSuchElementException:
            self.login_irida(driver, self.IRIDA_USER, self.IRIDA_PASSWORD)

    def login_irida(self, driver, username, password):
        """Log in to IRIDA (assumes the login page is opened by the driver)"""
        try:
            driver.find_element_by_id("emailTF").send_keys(username)
            driver.find_element_by_id(
                "passwordTF").send_keys(password)
            driver.find_element_by_id("submitBtn").click()
        except NoSuchElementException:
            # If already logged in
            pass

    def add_irida_client_auth_code(self, driver):
        driver.get(self.IRIDA_URL + '/clients/create')
        driver.find_element_by_id("clientId").send_keys(
            self.IRIDA_AUTH_CODE_ID)
        driver.find_element_by_id('authorizedGrantTypes').click()
        driver.find_element_by_xpath(
            "//*[contains(text(), 'authorization_code')]").click()
        driver.find_element_by_id("scope_auto_read").click()
        driver.find_element_by_id("create-client-submit").click()

    def add_irida_client_password(self, driver):
        driver.get(self.IRIDA_URL + '/clients/create')
        driver.find_element_by_id("clientId").send_keys(self.IRIDA_PASSWORD_ID)
        driver.find_element_by_id("scope_write").click()
        driver.find_element_by_id("create-client-submit").click()

    def get_irida_oauth(self, driver):
        secret = self.get_irida_secret(driver, self.IRIDA_PASSWORD_ID)
        client = LegacyApplicationClient(self.IRIDA_PASSWORD_ID)
        irida_oauth = OAuth2Session(client=client)
        irida_oauth.fetch_token(
            self.IRIDA_TOKEN_ENDPOINT,
            username=self.IRIDA_USER,
            password=self.IRIDA_PASSWORD,
            client_secret=secret)
        return irida_oauth

    def get_irida_secret(self, driver, client_id):
        """Get an IRIDA client's secret given its client ID """
        driver.get(self.IRIDA_URL + '/clients')
        driver.find_element_by_xpath(
            "//*[contains(text(), '" + client_id + "')]").click()
        secret = driver.find_element_by_id(
            'client-secret').get_attribute('textContent')
        return secret

    def configure_irida_client_secret(self, driver):
        """Configure the client secret for the tool"""
        secret = self.get_irida_secret(driver, self.IRIDA_AUTH_CODE_ID)
        # It is assumed that the tests are being run from the repo's tool
        # directory:
        self.configure_tool('IRIDA', 'client_secret', secret)

    def get_href(self, response, rel):
        """From a Requests response from IRIDA, get a href given a rel"""
        links = response.json()['resource']['links']
        href = next(link['href'] for link in links if link['rel'] == rel)
        return href

    def test_project_samples_import(self, setup_irida, setup_galaxy,
                                    driver, tmpdir):
        """Verify that sequence files can be imported from IRIDA to Galaxy"""
        irida = setup_irida
        project_name = 'ImportProjectSamples'
        project = irida.post(self.IRIDA_PROJECTS,
                             json={'name': project_name})

        samples = self.get_href(project, 'project/samples')
        sample1 = irida.post(samples, json={'sampleName': 'PS_Sample1',
                                            'sequencerSampleId': 'PS_1'})
        sequences1 = self.get_href(sample1, 'sample/sequenceFiles')

        # Pytest manages the temporary directory
        seq1 = tmpdir.join("seq1.fastq")
        seq1.write(self.FASTQ_CONTENTS)
        sequence1 = irida.post(sequences1, files={'file': open(str(seq1),
                               'rb')})

        seq2 = tmpdir.join("seq2.fastq")
        seq2.write(self.FASTQ_CONTENTS)
        sequence2 = irida.post(sequences1, files={'file': open(str(seq2),
                               'rb')})

        sample2 = irida.post(samples, json={'sampleName': 'PS_Sample2',
                                            'sequencerSampleId': 'PS_2'})
        sequences2 = self.get_href(sample2, 'sample/sequenceFiles')
        seq3 = tmpdir.join("seq3.fastq")
        seq3.write(self.FASTQ_CONTENTS)
        sequence3 = irida.post(sequences2, files={'file': open(str(seq3),
                               'rb')})

        # Export to Galaxy using the button on the dropdown menu
        driver.get(self.GALAXY_URL)
        history_panel = driver.find_element_by_id('current-history-panel')
        initially_succeeded = len(history_panel.find_elements_by_class_name(
            'state-ok'))
        driver.find_element_by_css_selector("#title_getext > a > span").click()
        driver.find_element_by_link_text("IRIDA server").click()

        # Sometimes a login is required
        try:
            self.login_irida(driver, self.IRIDA_USER, self.IRIDA_PASSWORD)
        except NoSuchElementException:
            pass

        # Pick the last matching project on this page
        driver.find_elements_by_link_text(project_name)[-1].click()

        # These checkbox elements cannot be clicked directly
        # Using IDs would complicate running the tests without restarting IRIDA
        action = webdriver.common.action_chains.ActionChains(driver)
        stale = True
        timeout = 0
        while stale:
            try:
                checkboxes = driver.find_elements_by_xpath("//table[contains(@id, 'samplesTable')]/tbody/tr/td[1]/input[@type='checkbox']")


                checkboxes[0].click()
                checkboxes[1].click()

                stale = False
            except (StaleElementReferenceException, NoSuchElementException):
                time.sleep(1)
                timeout += 1

                if timeout == 60:
                    raise

        driver.find_element_by_id("cart-add-btn").click()
        driver.find_element_by_id("cart-show-btn").click()

        email_input=driver.find_element_by_xpath("//form[contains(@class, 'ant-form')]//input[@type='text']")
        email_input.clear()
        email_input.send_keys(self.EMAIL)

        # Click "Export Samples to Galaxy" button
        driver.find_element_by_xpath("//button[span[text()='Export Samples to Galaxy']]").click()

        WebDriverWait(driver, self.WAIT).until(
            EC.presence_of_element_located((By.ID, 'current-history-panel'))
        )
        time.sleep(120)  # Wait for import to complete
        history_panel = driver.find_element_by_id('current-history-panel')
        succeeded = len(history_panel.find_elements_by_class_name('state-ok'))
        assert succeeded - initially_succeeded > 0, \
                "Import did not complete successfully"
