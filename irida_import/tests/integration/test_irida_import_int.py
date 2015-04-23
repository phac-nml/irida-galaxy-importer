import sys
import logging
import os
import pytest
import subprocess32
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from ...irida_import import IridaImport
import inspect
from . import util
import getpass
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import LegacyApplicationClient


@pytest.mark.integration
class TestIridaImportInt:

    TIMEOUT = 600  # seconds

    USER = getpass.getuser()

    GALAXY_DOMAIN = 'localhost'
    GALAXY_PORT = 8888
    GALAXY_URL = 'http://'+GALAXY_DOMAIN+':'+str(GALAXY_PORT)
    GALAXY_CMD = ['bash', 'run.sh']
    GALAXY_STOP = 'pkill -u '+USER+' -f "python ./scripts/paster.py"'
    GALAXY_DB_RESET = 'echo "drop database if exists external_galaxy_test;'\
        ' create database external_galaxy_test;'\
        '"| mysql -u test -ptest'

    IRIDA_DOMAIN = 'localhost'
    IRIDA_PORT = 8080
    IRIDA_URL = 'http://'+IRIDA_DOMAIN+':'+str(IRIDA_PORT)
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
    IRIDA_PASSWORD_ID = 'password_client_id'
    IRIDA_AUTH_CODE_ID = 'auth_code_client_id'
    IRIDA_USER = 'admin'
    IRIDA_PASSWORD = 'Password1'
    IRIDA_TOKEN_ENDPOINT = IRIDA_URL + '/api/oauth/token'

    INSTALL_EXEC = 'install.sh'

    def setup_class(self):
        """Initialize class variables, install IRIDA, Galaxy, and the tool"""
        module_dir = os.path.dirname(os.path.abspath(__file__))
        self.SCRIPTS = os.path.join(module_dir, 'bash_scripts')
        self.REPOS_PARENT = module_dir
        self.REPOS = os.path.join(module_dir, 'repos')
        self.TOOL_DIRECTORY = os.path.dirname(inspect.getfile(IridaImport))

        self.GALAXY = os.path.join(self.REPOS, 'galaxy')
        self.IRIDA = os.path.join(self.REPOS, 'irida')

        try:
            os.environ['IRIDA_GALAXY_TOOL_TESTS_DONT_INSTALL']
        except KeyError:
            # Install IRIDA, Galaxy, and the IRIDA export tool:
            exec_path = os.path.join(self.SCRIPTS, self.INSTALL_EXEC)
            install = subprocess32.Popen(
                [exec_path, self.TOOL_DIRECTORY], cwd=self.REPOS_PARENT)
            install.wait()  # Block untill installed

        log = logging.getLogger()
        log.setLevel(logging.DEBUG)
        log_out = logging.StreamHandler(sys.stdout)
        log_out.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        log_out.setFormatter(formatter)
        log.addHandler(log_out)

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
            print 'Stopping IRIDA nicely'
            stopper = subprocess32.Popen(self.IRIDA_STOP, cwd=self.IRIDA,
                                         shell=True)
            stopper.wait()

        try:
            os.environ['IRIDA_GALAXY_TOOL_TESTS_DONT_START_IRIDA']
        except KeyError:
            stop_irida()
            subprocess32.call(self.IRIDA_DB_RESET, shell=True)
            subprocess32.Popen(self.IRIDA_CMD, cwd=self.IRIDA)
            util.wait_until_up(self.IRIDA_DOMAIN, self.IRIDA_PORT, self.TIMEOUT)

            def finalize_irida():
                stop_irida()
            request.addfinalizer(finalize_irida)
        self.register_irida(driver)
        self.add_irida_client_auth_code(driver)
        self.add_irida_client_password(driver)

        irida_oauth = self.get_irida_oauth(driver)

        self.create_irida_project(irida_oauth, 'Project1')
        self.gen_seq_files_irida(
            irida_oauth, 'Project1', [
                'file1.fastq', 'file2.fasta'])

    @pytest.fixture(scope='class')
    def setup_galaxy(self, request, driver):
        """Set up Galaxy for tests (Start if required, register, log in)"""
        def stop_galaxy():
            print 'Killing Galaxy'
            subprocess32.call(self.GALAXY_STOP, shell=True)

        try:
            os.environ['IRIDA_GALAXY_TOOL_TESTS_DONT_START_GALAXY']
        except KeyError:
            stop_galaxy()
            subprocess32.call(self.GALAXY_DB_RESET, shell=True)
            subprocess32.Popen(self.GALAXY_CMD, cwd=self.GALAXY)
            util.wait_until_up(
                self.GALAXY_DOMAIN,
                self.GALAXY_PORT,
                self.TIMEOUT)

            def finalize_galaxy():
                stop_galaxy()
            request.addfinalizer(finalize_galaxy)
        self.register_galaxy(driver)

    def test_configured(self, setup_irida, setup_galaxy, driver):
        """Verify that IRIDA and Galaxy are both accessible"""
        driver.get(self.IRIDA_URL)
        driver.get(self.GALAXY_URL)

    def test_tool_visible(self, setup_galaxy, driver):
        """Make sure there is a link to the tool in Galaxy"""
        driver.get(self.GALAXY_URL)
        driver.find_element_by_css_selector("#title_getext > a > span").click()
        assert(driver.find_element_by_link_text("IRIDA"))

    def register_galaxy(self, driver):
        """Register with Galaxy"""
        driver.get(self.GALAXY_URL)
        driver.find_element_by_link_text("User").click()
        driver.find_element_by_link_text("Register").click()
        driver.switch_to_frame(driver.find_element_by_tag_name("iframe"))
        driver.find_element_by_id("email_input").send_keys("irida@irida.ca")
        driver.find_element_by_id("password_input").send_keys("Password1")
        driver.find_element_by_id("password_check_input").send_keys("Password1")
        driver.find_element_by_id("name_input").send_keys("irida-test")
        driver.find_element_by_id("send").click()

    def register_irida(self, driver):
        """Register with IRIDA if neccessary, and then log in"""
        driver.get(self.IRIDA_URL)

        # Log in if possible
        try:
            driver.find_element_by_id("emailTF").send_keys("admin")
            driver.find_element_by_id("passwordTF").send_keys("password1")
            driver.find_element_by_id("submitBtn").click()

            # Set a new password if necessary
            try:
                driver.find_element_by_id("password").send_keys(self.IRIDA_PASSWORD)
                driver.find_element_by_id(
                    "confirmPassword").send_keys(self.IRIDA_PASSWORD)
                driver.find_element_by_xpath("//button[@type='submit']").click()
            except NoSuchElementException:
                driver.find_element_by_id("emailTF").send_keys(self.IRIDA_USER)
                driver.find_element_by_id("passwordTF").send_keys(self.IRIDA_PASSWORD)
                driver.find_element_by_id("submitBtn").click()
        except NoSuchElementException:
            pass

    def add_irida_client_auth_code(self, driver):
        driver.get(self.IRIDA_URL + '/clients/create')
        driver.find_element_by_id("clientId").send_keys(self.IRIDA_AUTH_CODE_ID)
        driver.find_element_by_id('s2id_authorizedGrantTypes').click()
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
        driver.get(self.IRIDA_URL + '/clients')
        driver.find_element_by_xpath(
            "//*[contains(text(), '"+self.IRIDA_PASSWORD_ID+"')]").click()
        secret = driver.find_element_by_id(
            'client-secret').get_attribute('textContent')
        client = LegacyApplicationClient(self.IRIDA_PASSWORD_ID)
        irida_oauth = OAuth2Session(client=client)
        irida_oauth.fetch_token(
            self.IRIDA_TOKEN_ENDPOINT,
            client_id=self.IRIDA_PASSWORD_ID,
            username=self.IRIDA_USER,
            password=self.IRIDA_PASSWORD,
            client_secret=secret)
        return irida_oauth

    def create_irida_project(self, irida_oauth, name):
        """Create a new IRIDA project, using an OAuth2 session"""
        url = self.IRIDA_URL + '/api/projects'
        payload = {'name': name}
        r = irida_oauth.post(url, json=payload)
        r.raise_for_status()
        return r.json()

    def create_irida_sample(self, irida_oauth, samples_url, name):
        """Create a new IRIDA sample, using an OAuth2 session"""
        payload = {'name': name}
        r = irida_oauth.post(samples_url, json=payload)
        r.raise_for_status()

    def create_irida_seqfile(self, irida_oauth, seqfile_url, name, file_path):
        payload = {'name': name}
        r = irida_oauth.post(samples_url, json=payload)
        r.raise_for_status()

    def gen_seq_files_irida(self, irida_oauth, sample_url, seq_file_name_list):
        """Generate sequence files in an IRIDA project from a list of names"""
        url = self.IRIDA_URL + ''
        return True
