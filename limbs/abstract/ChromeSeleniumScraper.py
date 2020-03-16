"""
Abstract module for scraping using Selenium Webdriver and Chrome
"""

import os

from centipede.limbs.abstract.Limb import Limb
from centipede.limbs.common import proxy_servers, user_agents

from selenium.webdriver import ChromeOptions
from selenium import webdriver
from selenium.common.exceptions import TimeoutException


class ChromeSeleniumScraper(Limb):

    MAX_RETRIES = 5

    def __init__(self, config_dict):
        """
        Like Limb, this class is not meant to be instantiated.
        """

        super(ChromeSeleniumScraper, self).__init__(config_dict)

        self.is_spoofing_user_agent = False
        if config_dict.get("SPOOF_USER_AGENT", False):
            self.is_spoofing_user_agent = True

        self.is_using_proxy_server = False
        if config_dict.get("USE_PROXY_SERVER", False):
            self.is_using_proxy_server = True

        self.uagent = None
        if self.is_spoofing_user_agent:
            self.uagent = user_agents.get_user_agent_string()

        self.proxy_server = None
        if self.is_using_proxy_server:
            self.proxy_server = proxy_servers.pop()

        self.logger = config_dict["logger"]

        self.verify_chrome_on_path()
        self.driver = self._init_selenium_driver_chrome(self.uagent, self.proxy_server)


    def verify_chrome_on_path(self):
        """
        Adjusts the PATH system variable to ensure that the geckodriver executable is recognized.
        """
        path_value = os.environ["PATH"]
        path_values = path_value.split(";")

        path_contains_chrome_binary = False
        for path in path_values:
            if path.endswith("centipede\\limbs\\common"):
                path_contains_chrome_binary = True

        if not path_contains_chrome_binary:
            cwd = "" # TODO - insert relative path to chromedriver, independent of the cwd.
            os.environ["PATH"] = cwd + ";" + os.environ["PATH"]


    def _init_selenium_driver_chrome(self, uagent, proxy_server):
        """
        Initializes and returns the selenium webdriver, using the Chrome binary.
        """
        options = ChromeOptions()
        prefs = {"profile.managed_default_content_settings.images": 2,
                 "profile.default_content_setting_values.notifications": 2}
        options.add_experimental_option("prefs", prefs)
        # options.add_argument("--headless")
        options.add_argument("start-maximized")

        if proxy_server:
            proxy_address = proxy_server[0]
            proxy_port = str(proxy_server[1])
            proxy_protocol = proxy_server[2]
            print("--proxy-server=" + proxy_protocol + "://" + proxy_address + ":" + proxy_port)
            options.add_argument("--proxy-server=" + proxy_protocol + "://" + proxy_address + ":" + proxy_port)

        if uagent:
            options.add_argument("--user-agent=" + uagent)
            print("--user-agent=" + uagent)

        self.driver = webdriver.Chrome("chromedriver.exe", chrome_options=options)
        self.driver.set_page_load_timeout(120)
        return self.driver


    def scrape_from_url(self, url, package):
        """
        Given a url string, ingests information from that URL.
        Branches into different methods depending on structure of URL.
        Returns a dictionry of information scraped / determined.
        """
        for regex in self.regex_to_scraping_method:
            match = regex.match(url)
            if match:
                scraping_method = self.regex_to_scraping_method[regex]

                num_retries = 0
                while num_retries < ChromeSeleniumScraper.MAX_RETRIES:
                    try:
                        package = scraping_method(url, package)
                        break
                    except TimeoutException:
                        num_retries += 1
                        proxy_servers.put_back(self.proxy_server)
                        self.proxy_server = proxy_servers.pop()
                        self.driver = self._init_selenium_driver_chrome(self.uagent, self.proxy_server)

        return package

    def wait_for_xpath(self, xpath):
        """
        Waits a given amount of time for an element to appear on the page.
        If it does not appear, throw a Selenium TimeoutException.
        """
        pass # TODO - implement this based on deployed code.