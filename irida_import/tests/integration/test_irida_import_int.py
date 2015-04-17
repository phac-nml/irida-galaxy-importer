import os
import pytest
import subprocess32
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from ...irida_import import IridaImport
import inspect
from . import util
import getpass


@pytest.mark.integration
class TestIridaImportInt:

    INSTALL = True  # Install or update Galaxy, IRIDA, and the export tool
    START_GALAXY = True  # Start Galaxy instance
    START_IRIDA = True  # Start IRIDA instance

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

    INSTALL_EXEC = 'install.sh'

    def setup_class(self):
        module_dir = os.path.dirname(os.path.abspath(__file__))
        self.SCRIPTS = os.path.join(module_dir, 'bash_scripts')
        self.REPOS_PARENT = module_dir
        self.REPOS = os.path.join(module_dir, 'repos')
        self.TOOL_DIRECTORY = os.path.dirname(inspect.getfile(IridaImport))

        self.GALAXY = os.path.join(self.REPOS, 'galaxy')
        self.IRIDA = os.path.join(self.REPOS, 'irida')

        if self.INSTALL:
            # Install IRIDA, Galaxy, and the IRIDA export tool:
            exec_path = os.path.join(self.SCRIPTS, self.INSTALL_EXEC)
            install = subprocess32.Popen(
                [exec_path, self.TOOL_DIRECTORY], cwd=self.REPOS_PARENT)
            install.wait()  # Block untill installed

    @pytest.fixture(scope='class')
    def driver(self, request):
        driver = webdriver.Chrome()
        driver.implicitly_wait(5)

        def finalize_driver():
            driver.quit()
        request.addfinalizer(finalize_driver)
        return driver

    @pytest.fixture(scope='class')
    def setup_irida(self, request, driver):
        def stop_irida():
            print 'Stopping IRIDA nicely'
            stopper = subprocess32.Popen(self.IRIDA_STOP, cwd=self.IRIDA,
                                         shell=True)
            stopper.wait()

        if self.START_IRIDA:
            stop_irida()
            subprocess32.call(self.IRIDA_DB_RESET, shell=True)
            subprocess32.Popen(self.IRIDA_CMD, cwd=self.IRIDA)
            util.wait_until_up(self.IRIDA_DOMAIN, self.IRIDA_PORT, self.TIMEOUT)

            def finalize_irida():
                stop_irida()
            request.addfinalizer(finalize_irida)
        self.register_irida(driver)

    @pytest.fixture(scope='class')
    def setup_galaxy(self, request, driver):
        def stop_galaxy():
            print 'Killing Galaxy'
            subprocess32.call(self.GALAXY_STOP, shell=True)

        if self.START_GALAXY:
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
        driver.get(self.IRIDA_URL)
        driver.get(self.GALAXY_URL)

    def test_tool_visible(self, setup_galaxy, driver):
        driver.get(self.GALAXY_URL)
        driver.find_element_by_css_selector("#title_getext > a > span").click()
        assert(driver.find_element_by_link_text("IRIDA"))

    def register_galaxy(self, driver):
        driver.save_screenshot('/Warehouse/Temporary/jthiessen/gal0')
        driver.get(self.GALAXY_URL)
        driver.save_screenshot('/Warehouse/Temporary/jthiessen/gal1')
        driver.get(self.GALAXY_URL)
        driver.save_screenshot('/Warehouse/Temporary/jthiessen/gal2')
        driver.find_element_by_link_text("User").click()
        driver.save_screenshot('/Warehouse/Temporary/jthiessen/gal3')
        driver.find_element_by_link_text("Register").click()
        driver.switch_to_frame(driver.find_element_by_tag_name("iframe"))
        driver.find_element_by_id("email_input").send_keys("irida@irida.ca")
        driver.find_element_by_id("password_input").send_keys("Password1")
        driver.find_element_by_id("password_check_input").send_keys("Password1")
        driver.find_element_by_id("name_input").send_keys("irida-test")
        driver.find_element_by_id("send").click()

    def register_irida(self, driver):
        driver.get(self.IRIDA_URL)
        driver.find_element_by_id("emailTF").send_keys("admin")
        driver.find_element_by_id("passwordTF").send_keys("password1")
        driver.find_element_by_id("submitBtn").click()
        try:
            driver.find_element_by_id("password").send_keys("Password1")
            driver.find_element_by_id("confirmPassword").send_keys("Password1")
            driver.find_element_by_xpath("//button[@type='submit']").click()
        except NoSuchElementException:
            driver.find_element_by_id("emailTF").send_keys("admin")
            driver.find_element_by_id("passwordTF").send_keys("Password1")
            driver.find_element_by_id("submitBtn").click()
