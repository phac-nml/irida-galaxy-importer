"""
This file is responsible for Managing an IRIDA instance, including all the parameters associated with testing and
database management.
"""

import logging
from os import path
from time import time, sleep
import sys
import subprocess
import inspect
import socket

from ...irida_import import IridaImport


class SetupGalaxyData:

    def __init__(self, repo_dir):

        self.log = self._setup_galaxy_logger()

        module_dir = path.dirname(path.abspath(__file__))
        self.SCRIPTS = path.join(module_dir, 'bash_scripts')
        self.REPOS_PARENT = module_dir
        self.REPOS = repo_dir
        self.GALAXY_REPO = path.join(self.REPOS, 'galaxy')
        self.TOOL_DIRECTORY = path.dirname(inspect.getfile(IridaImport))
        self.CONFIG_PATH = path.join(self.TOOL_DIRECTORY, 'tests',
                                     'integration', 'repos', 'galaxy',
                                     'tools', 'irida-galaxy-importer', 'irida_import',
                                     'config.ini')
        self.INSTALL_EXEC = 'install_galaxy.sh'
        self.GALAXY_DOMAIN = 'localhost'
        self.GALAXY_PORT = 8888
        self.GALAXY_URL = 'http://' + self.GALAXY_DOMAIN + ':' + str(
            self.GALAXY_PORT)
        self.CONDA_INIT = '. $CONDA_PREFIX/etc/profile.d/conda.sh && conda activate _galaxy_ && '
        self.GALAXY_STOP = self.CONDA_INIT + 'bash run.sh --stop-daemon'
        self.GALAXY_DB_RESET = 'echo "drop database if exists galaxy_test; create database galaxy_test;" | psql'
        self.GALAXY_RUN = self.CONDA_INIT + 'bash run.sh --daemon'

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

    def setup_galaxy(self):
        """
        Stops galaxy, resets db, and starts it up again
        :return:
        """
        # reset the galaxy database
        self.log.info("Resetting galaxy database")
        subprocess.call(self.GALAXY_DB_RESET, shell=True)

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
