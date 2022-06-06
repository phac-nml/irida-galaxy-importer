"""
Runs integration tests via selenium
"""
import time
import unittest
import ast
import tempfile
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin
from rauth import OAuth2Service

import irida_import.tests.integration.tests_integration as tests_integration


class IridaImporterTestSuite(unittest.TestCase):

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)
        self.driver = self._init_driver()
        self.irida_session = self._get_irida_oauth_session()

    def tearDown(self):
        self.driver.quit()
        return

    @staticmethod
    def _init_driver():
        """Set up the Selenium WebDriver"""
        driver = webdriver.Chrome(tests_integration.chrome_driver_path, options=tests_integration.chrome_driver_options)
        driver.implicitly_wait(1)
        driver.set_window_size(1024, 768)

        return driver

    @staticmethod
    def _get_irida_oauth_session():
        def token_decoder(return_dict):
            """
            safely parse given dictionary

            arguments:
                return_dict -- access token dictionary

            returns evaluated dictionary
            """
            # It is supposedly safer to decode bytes to string and then use ast.literal_eval than just use eval()
            try:
                irida_dict = ast.literal_eval(return_dict.decode("utf-8"))
            except (SyntaxError, ValueError):
                # SyntaxError happens when something that looks nothing like a token is returned (ex: 404 page)
                # ValueError happens with the path returns something that looks like a token, but is invalid
                #   (ex: forgetting the /api/ part of the url)
                raise ConnectionError("Unexpected response from server, URL may be incorrect")
            return irida_dict

        access_token_url = urljoin(tests_integration.irida_base_url, "oauth/token")
        oauth_service = OAuth2Service(
            client_id=tests_integration.client_id,
            client_secret=tests_integration.client_secret,
            name="irida",
            access_token_url=access_token_url,
            base_url=tests_integration.irida_base_url
        )

        params = {
            "data": {
                "grant_type": "password",
                "client_id": tests_integration.client_id,
                "client_secret": tests_integration.client_secret,
                "username": tests_integration.username,
                "password": tests_integration.password
            }
        }

        access_token = oauth_service.get_access_token(
            decoder=token_decoder, **params)

        return oauth_service.get_session(access_token)

    def test_irida_alive(self):
        """
        Tests an endpoint on irida to check alive status
        :return:
        """
        try:
            url = f"{tests_integration.irida_base_url}projects"
            response = self.irida_session.get(url)
            print(response)
        except Exception as e:
            self.fail("Could not verify that IRIDA is up: " + str(e))

    def test_galaxy_alive(self):
        """
        Tests an endpoint on galaxy to check alive status
        :return:
        """
        try:
            response = self.driver.get(tests_integration.galaxy_url)
            print(response)
        except Exception as e:
            self.fail("Could not verify that IRIDA is up: " + str(e))

    def test_tool_visible(self):
        """Make sure there is a link to the tool in Galaxy"""
        self.driver.get(tests_integration.galaxy_url)
        self.driver.find_element_by_xpath("//a[span[contains(text(), 'Get Data')]]").click()
        self.assertIsNotNone(self.driver.find_element_by_xpath("//a[span[contains(text(), 'IRIDA')]]"))

    def test_project_samples_import_single_end(self):
        """Verify that sequence files can be imported from IRIDA to Galaxy"""

        def _get_href(response, rel):
            """From a Requests response from IRIDA, get a href given a rel"""
            links = response.json()['resource']['links']
            href = next(link['href'] for link in links if link['rel'] == rel)
            return href

        def _create_temp_file(file_name, file_contents):
            """Create a fake file in memory with a wilename and file contents, returns file path"""
            tmp = tempfile.NamedTemporaryFile(delete=False)
            path = tmp.name
            tmp.name = file_name
            tmp.write(str.encode(file_contents))
            return path

        fastq_contents = (
            "@SRR566546.970 HWUSI-EAS1673_11067_FC7070M:4:1:2299:1109 length=50\n" +
            "TTGCCTGCCTATCATTTTAGTGCCTGTGAGGTGGAGATGTGAGGATCAGT\n" +
            "+SRR566546.970 HWUSI-EAS1673_11067_FC7070M:4:1:2299:1109 length=50\n" +
            "hhhhhhhhhhghhghhhhhfhhhhhfffffe`ee[`X]b[d[ed`[Y[^Y")

        project_name = 'ImportProjectSamples'
        project = self.irida_session.post(f"{tests_integration.irida_base_url}projects",
                                          json={'name': project_name})

        samples = _get_href(project, 'project/samples')
        sample1 = self.irida_session.post(samples, json={'sampleName': 'PS_Sample1','sequencerSampleId': 'PS_1'})
        sequences1 = _get_href(sample1, 'sample/sequenceFiles')

        seq1 = _create_temp_file("seq1.fastq", fastq_contents)
        self.irida_session.post(sequences1, files={'file': open(seq1, 'rb')})

        seq2 = _create_temp_file("seq2.fastq", fastq_contents)
        self.irida_session.post(sequences1, files={'file': open(seq2, 'rb')})

        sample2 = self.irida_session.post(samples, json={'sampleName': 'PS_Sample2', 'sequencerSampleId': 'PS_2'})
        sequences2 = _get_href(sample2, 'sample/sequenceFiles')

        seq3 = _create_temp_file("seq3.fastq", fastq_contents)
        self.irida_session.post(sequences2, files={'file': open(seq3, 'rb')})

        # Export to Galaxy using the button on the dropdown menu
        self.driver.get(tests_integration.galaxy_url)
        history_panel = self.driver.find_element_by_id('current-history-panel')
        initially_succeeded = len(history_panel.find_elements_by_class_name('state-ok'))
        self.driver.find_element_by_xpath("//a[span[contains(text(), 'Get Data')]]").click()
        self.driver.find_element_by_xpath("//a[span[contains(text(), 'IRIDA')]]").click()

        # Sometimes a login is required
        try:
            self.driver.find_element_by_name("username").send_keys(tests_integration.username)
            self.driver.find_element_by_name("password").send_keys(tests_integration.password)
            self.driver.find_element_by_xpath("//button[@type='submit']").click()
        except NoSuchElementException:
            # If already logged in
            pass

        # Pick the last matching project on this page
        self.driver.find_elements_by_link_text(project_name)[-1].click()

        stale = True
        timeout = 0
        while stale:
            try:
                checkboxes = self.driver.find_elements_by_xpath("//input[@type='checkbox']")
                # first checkbox is "select all samples checkbox"
                checkboxes[0].click()
                stale = False
            except (StaleElementReferenceException, NoSuchElementException):
                time.sleep(1)
                timeout += 1

                if timeout == 60:
                    raise

        self.driver.find_elements_by_class_name("t-add-cart-btn")[0].click()
        time.sleep(10)  # wait 10 seconds for popup to disappear
        self.driver.find_element_by_xpath("//a[@href='/cart/galaxy']").click()

        email_input = self.driver.find_element_by_xpath("//form[contains(@class, 'ant-form')]//input[@type='text']")
        email_input.send_keys(Keys.CONTROL, "a")
        email_input.send_keys(tests_integration.galaxy_email)

        # Click "Export Samples to Galaxy" button
        self.driver.find_element_by_xpath("//button[span[text()='Export Samples to Galaxy']]").click()

        # handle auth confirmation popup
        if len(self.driver.window_handles) > 1:
            self.driver.switch_to.window(self.driver.window_handles[1])
            self.driver.find_element_by_id('authorize-btn').click()
            self.driver.switch_to.window(self.driver.window_handles[0])

        WebDriverWait(self.driver, 120).until(
            EC.presence_of_element_located((By.ID, 'current-history-panel'))
        )
        time.sleep(120)  # Wait for import to complete
        history_panel = self.driver.find_element_by_id('current-history-panel')
        succeeded = len(history_panel.find_elements_by_class_name('state-ok'))
        # This currently fails, as the tool is broken because of this following issue
        # https://github.com/galaxyproject/galaxy/issues/11066
        self.assertTrue(succeeded - initially_succeeded > 0, "Import did not complete successfully")
