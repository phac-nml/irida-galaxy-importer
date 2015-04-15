import os
import pytest
import subprocess32
from splinter import Browser
from ...irida_import import IridaImport
import inspect
from . import util
import getpass


@pytest.mark.integration
class TestIridaImportInt:

    INSTALL = True  # Install or update Galaxy, IRIDA, and the export tool
    START = True  # Start Galaxy and IRIDA instances

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
    def browser(self, request):
        browser = Browser('chrome')

        def finalize_browser():
            browser.quit()
        request.addfinalizer(finalize_browser)
        return browser

    @pytest.fixture(scope='class')
    def setup_irida(self, request, browser):
        def stop_irida():
            print 'Stopping IRIDA nicely'
            stopper = subprocess32.Popen(self.IRIDA_STOP, cwd=self.IRIDA,
                                         shell=True)
            stopper.wait()

        if self.START:
            stop_irida()
            subprocess32.call(self.IRIDA_DB_RESET, shell=True)
            subprocess32.Popen(self.IRIDA_CMD, cwd=self.IRIDA)
            util.wait_until_up(self.IRIDA_DOMAIN, self.IRIDA_PORT, self.TIMEOUT)

            def finalize_irida():
                stop_irida()
            request.addfinalizer(finalize_irida)
        self.register_irida(browser)

    @pytest.fixture(scope='class')
    def setup_galaxy(self, request, browser):
        def stop_galaxy():
            print 'Killing Galaxy'
            subprocess32.call(self.GALAXY_STOP, shell=True)

        if self.START:
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
        self.register_galaxy(browser)

    def test_configured(self, setup_irida, setup_galaxy, browser):
        browser.visit(self.IRIDA_URL)
        browser.visit(self.GALAXY_URL)

    def test_tool_visible(self, setup_galaxy, browser):
        get_data = browser.find_by_css('#title_getext a')
        get_data.click()
        browser.is_element_present_by_name('IRIDA')
        # Don't click the link, Splinter/Selenium will hang

    def register_galaxy(self, browser):
        browser.visit(self.GALAXY_URL)
        browser.find_link_by_text("User").click()
        browser.find_link_by_text("Register").click()
        browser.find_by_id("email_input").fill("irida@irida.ca")
        browser.find_by_id("password_input").clear()
        browser.find_by_id("password_input").fill("Password1")
        browser.find_by_id("password_check_input").fill("Password1")
        browser.find_by_id("name_input").fill("irida-test")
        browser.find_by_id("send").click()

    def register_irida(self, browser):
        browser.visit(self.IRIDA_URL)
        browser.find_by_id("emailTF").fill("admin")
        browser.find_by_id("passwordTF").fill("password1")
        browser.find_by_id("submitBtn").click()
        browser.find_by_id("password").fill("Password1")
        browser.find_by_id("confirmPassword").fill("Password1")
        browser.find_by_xpath("//button[@type='submit']").click()
