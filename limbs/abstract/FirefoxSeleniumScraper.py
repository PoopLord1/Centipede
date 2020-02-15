"""
Abstract module for scraping using Selenium Webdriver and Firefox
"""

import os

from .Limb import Limb
from centipede.limbs.common import proxy_servers, user_agents

from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException


class FirefoxSeleniumScraper(Limb):

    MAX_RETRIES = 5

    def __init__(self, config_dict):
        """
        Like Limb, this class is not meant to be instantiated.
        """

        super(FirefoxSeleniumScraper, self).__init__(config_dict)

        self.driver = None
        self.uagent = None
        self.proxy_server = None

        self.is_spoofing_user_agent = False
        if config_dict.get("SPOOF_USER_AGENT", False):
            self.is_spoofing_user_agent = True

        self.is_using_proxy_server = False
        if config_dict.get("USE_PROXY_SERVER", False):
            self.is_using_proxy_server = True

        if self.is_spoofing_user_agent:
            self.uagent = user_agents.get_user_agent_string()
        if self.is_using_proxy_server:
            self.proxy_server = proxy_servers.pop()

        self.ff_binary_location = config_dict["ff_binary_location"]

        self.verify_geckodriver_on_path()
        self.driver = self.init_selenium_driver_firefox(self.uagent, self.proxy_server)

    def verify_geckodriver_on_path(self):
        """
        Adjusts the PATH system variable to ensure that the geckodriver executable is recognized.
        """
        path_value = os.environ["PATH"]

        path_values = path_value.split(":")

        path_contains_geckodriver = False
        for path in path_values:
            if path.endswith(""):
                path_contains_geckodriver = True

        if not path_contains_geckodriver:
            cwd = os.getcwd()
            os.environ["PATH"] = cwd + ":" + os.environ["PATH"]


    def init_selenium_driver_firefox(self, uagent, proxy_server):
        """
        Initializes and returns the selenium webdriver, using Firefox.
        """
        binary = FirefoxBinary(self.ff_binary_location)

        path_value = os.environ["PATH"]
        path_values = path_value.split(":")

        firefox_capabilities = webdriver.DesiredCapabilities.FIREFOX
        firefox_capabilities['marionette'] = True

        profile = webdriver.FirefoxProfile()

        if proxy_server:
            proxy_server_address = proxy_server[0]
            proxy_server_port = proxy_server[1]
            proxy_server_protocol = proxy_server[2]

            if proxy_server_protocol == "SOCKS5":
                self.logger.info(
                    "Enabling SOCKS proxy server connected at " + proxy_server_address + ":" + str(proxy_server_port))
                profile.set_preference("network.proxy.type", 1)
                profile.set_preference("network.proxy.socks", proxy_server_address)
                profile.set_preference("network.proxy.socks_port", proxy_server_port)
                profile.set_preference("network.proxy.socks_version", 5)
            elif proxy_server_protocol == "HTTP":
                self.logger.info(
                    "Enabling HTTP proxy server connected at " + proxy_server_address + ":" + str(proxy_server_port))
                profile.set_preference("network.proxy.type", 1)
                profile.set_preference("network.profile.http", proxy_server_address)
                profile.set_preference("network.profile.http_port", proxy_server_port)

        if uagent:
            profile.set_preference("general.useragent.override", uagent)

        profile.set_preference("permissions.default.image", 2)
        # profile.set_preference("dom.ipc.plugins.enabled.libflashplayer.so", "false")
        profile.update_preferences()

        options = Options()
        options.headless = True

        driver = webdriver.Firefox(firefox_binary=binary, firefox_profile=profile, options=options)
        driver.set_page_load_timeout(120)

        return driver


    def scrape_from_url(self, url):
        """
        Given a url string, ingests information from that URL.
        Branches into different methods depending on structure of URL.
        Returns a dictionry of information scraped / determined.
        """
        output_data = {}
        for regex in self.regex_to_scraping_method:
            match = regex.match(url)
            if match:
                scraping_method = self.regex_to_scraping_method[regex]

                num_retries = 0
                while num_retries < FirefoxSeleniumScraper.MAX_RETRIES:
                    try:
                        output_data.update(scraping_method(url))
                    except TimeoutException:
                        num_retries += 1
                        proxy_servers.put_back(self.proxy_server)
                        self.proxy_server = proxy_servers.pop()
                        self.driver = self.init_selenium_driver_firefox(self.uagent, self.proxy_server)

        return output_data


    def wait_for_xpath(self, xpath):
        """
        Waits a given amount of time for an element to appear on the page.
        If it does not appear, throw a Selenium TimeoutException.
        """
        pass  # TODO - implement this based on deployed code.
