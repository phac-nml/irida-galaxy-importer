"""
This file is responsible for Managing an IRIDA instance, including all the parameters associated with testing and
database management.
"""

import logging
import configparser
from os import path
from time import time, sleep
import sys
import subprocess
import inspect
import socket
from selenium import webdriver
from selenium.common import exceptions as selenium_exceptions
from bioblend import galaxy as bioblend_galaxy

from ...irida_import import IridaImport


class SetupGalaxyData:

    def __init__(self, repo_dir, email, chrome_driver_path):

        self.log = self._setup_galaxy_logger()

        module_dir = path.dirname(path.abspath(__file__))
        self.SCRIPTS = path.join(module_dir, 'bash_scripts')
        self.REPOS_PARENT = module_dir
        self.REPOS = repo_dir
        self.GALAXY_REPO = path.join(self.REPOS, 'galaxy')
        self.TOOL_DIRECTORY = path.dirname(inspect.getfile(IridaImport))
        self.CONFIG_PATH = path.join(self.GALAXY_REPO,
                                     'tools', 'irida-galaxy-importer', 'irida_import',
                                     'config.ini')
        self.INSTALL_EXEC = 'install_galaxy.sh'
        self.GALAXY_DOMAIN = 'localhost'
        self.GALAXY_PORT = 8888
        self.GALAXY_URL = 'http://' + self.GALAXY_DOMAIN + ':' + str(
            self.GALAXY_PORT)
        self.CONDA_INIT = '. $CONDA_PREFIX/etc/profile.d/conda.sh && conda activate _galaxy_ && '
        self.GALAXY_STOP = self.CONDA_INIT + 'bash run.sh --stop-daemon'
        self.GALAXY_RUN = self.CONDA_INIT + 'bash run.sh --daemon'

        self.GALAXY_EMAIL = email
        self.GALAXY_PASSWORD = 'Password1'
        # defined in create_client.sql
        self.REDIRECT_CLIENT_SECRET = "auth_code_secret"

        self.CHROME_DRIVER_PATH = chrome_driver_path

    @staticmethod
    def _setup_galaxy_logger():
        log = logging.getLogger()
        log.setLevel(logging.DEBUG)
        log_out = logging.StreamHandler(sys.stdout)
        log_out.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        log_out.setFormatter(formatter)
        log.addHandler(log_out)
        return log

    def install_galaxy(self):
        """
        Installs Galaxy and blocks until up
        :return:
        """
        # Install Galaxy and the IRIDA export tool:
        exec_path = path.join(self.SCRIPTS, self.INSTALL_EXEC)
        install = subprocess.Popen([exec_path, self.TOOL_DIRECTORY,
                                    str(self.GALAXY_PORT)],
                                   cwd=self.REPOS_PARENT)
        install.wait()  # Block until installed

    def stop_galaxy(self):
        self.log.info('Killing Galaxy')
        subprocess.Popen(self.GALAXY_STOP, shell=True, cwd=self.GALAXY_REPO)

    def start_galaxy(self):
        self.log.info("Running galaxy")
        subprocess.Popen(self.GALAXY_RUN, shell=True, cwd=self.GALAXY_REPO)
        self.log.debug("Waiting for Galaxy database migration [%s]. Sleeping for [%s] seconds", self.GALAXY_URL, 360)
        sleep(360)
        self.log.debug("Galaxy database migration should have (hopefully) finished, checking if it is up")
        self._wait_until_up(
            self.GALAXY_DOMAIN,
            self.GALAXY_PORT,
            600)
        self.log.debug("Galaxy should now be up on [%s]", self.GALAXY_URL)

    def _wait_until_up(self, address, port, timeout):
        """
        Wait until a port at an address is occupied, or time out

        :type address: str
        :param address: e.g. 'localhost' or '127.0.0.1'
        :type port: int
        :param port: e.g. 8888
        :type timeout: int
        :param timeout: the time to wait in seconds until throwing an exception
        """

        def check_up(addr, p):
            """
            Find out if a port at an address is occupied
            """
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex((addr, p))
            sock.close()
            if result == 0:
                ans = True
            else:
                ans = False
            return ans

        max_time = time() + timeout
        up = False
        while not up and time() < max_time:
            self.log.debug("Checking if Galaxy is up...")
            up = check_up(address, port)

            # If we query Galaxy immediately it may reset the connection:
            sleep(10)

        if not up:
            raise Exception('There was no response at {} on port {} for {} seconds'
                            .format(address, port, timeout))

    def register_galaxy(self):
        """Register with Galaxy, and then attempt to log in"""
        driver = self._get_webdriver()

        try:
            driver.get(self.GALAXY_URL)
            driver.find_element_by_link_text("Login or Register").click()
            driver.find_element_by_id("register-toggle").click()
            driver.find_element_by_name("email").send_keys(self.GALAXY_EMAIL)
            driver.find_element_by_name("password").send_keys(self.GALAXY_PASSWORD)
            driver.find_element_by_name("confirm").send_keys(self.GALAXY_PASSWORD)
            driver.find_element_by_name("username").send_keys("irida-test")
            driver.find_element_by_name("create").click()

            driver.get(self.GALAXY_URL)
            driver.find_element_by_link_text("Login or Register").click()
            driver.find_element_by_name("login").send_keys(self.GALAXY_EMAIL)
            driver.find_element_by_name("password").send_keys(self.GALAXY_PASSWORD)
            driver.find_element_by_xpath("//button[@name='login']").click()
            driver.find_element_by_name("login").click()
        except selenium_exceptions.NoSuchElementException:
            pass
        finally:
            driver.quit()

    def configure_galaxy_api_key(self):
        """Make a new Galaxy admin API key and configure the tool to use it"""
        gal = bioblend_galaxy.GalaxyInstance(
            self.GALAXY_URL,
            email=self.GALAXY_EMAIL,
            password=self.GALAXY_PASSWORD)
        self.configure_tool('Galaxy', 'admin_key', gal.key)
        self.log.info('Galaxy admin_key:' + gal.key)

    def configure_irida_galaxy_connection(self, galaxy_url):
        """configures the tool to know the redirect secret for the irida->galaxy connection"""
        self.configure_tool('IRIDA', 'client_secret', self.REDIRECT_CLIENT_SECRET)
        self.configure_tool('Galaxy', 'galaxy_url', galaxy_url)

    def configure_tool(self, section, option, value):
        """Write tool configuration data"""
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH)
        config.set(section, option, value)
        with open(self.CONFIG_PATH, 'w') as config_file:
            config.write(config_file)

    def _get_webdriver(self):
        """Set up the Selenium WebDriver"""
        driver = webdriver.Chrome(self.CHROME_DRIVER_PATH)
        driver.implicitly_wait(1)
        driver.set_window_size(1024, 768)

        return driver
