"""
deep_copy_page.py - A Limb that accepts
"""

import re
import requests
import urllib
import base64
from bs4 import BeautifulSoup

from centipede.limbs.abstract.Limb import Limb
from centipede import user_agents
from centipede import proxy_servers
from centipede.package import Package

class DeepCopyPage(Limb):

    url_re = re.compile("([^/]+)?:?(//)?([^/]+)?([^$]*)")

    def __init__(self, config_dict):

        super(DeepCopyPage, self).__init__(config_dict)

        self.uagent = None
        if config_dict.get("SPOOF_USER_AGENT", False):
            self.uagent = user_agents.get_user_agent_string()

        self.proxy_server = None
        if config_dict.get("USE_PROXY_SERVER", False):
            self.proxy_server = proxy_servers.pop()

        wildcard_re = re.compile("^")
        self.associate_regex_with_method(wildcard_re, self.deep_copy_page)

    @staticmethod
    def globalize_url(original_page, relative_url):
        orig_match = DeepCopyPage.url_re.match(original_page)
        relative_match = DeepCopyPage.url_re.match(relative_url)

        orig_tokens = [orig_match.group(1), orig_match.group(2), orig_match.group(3), orig_match.group(4)]
        relative_tokens = [relative_match.group(1), relative_match.group(2), relative_match.group(3), relative_match.group(4)]

        global_tokens = []
        for i, rel_token in enumerate(relative_tokens):
            if not rel_token:
                global_tokens.append(orig_tokens[i])
            else:
                global_tokens.append(rel_token)

        return global_tokens

    def deep_copy_page(self, page, data_package):

        rand_proxy = proxy_servers.pop()
        proxies = {rand_proxy[2]: rand_proxy[0] + ":" + str(rand_proxy[1])}
        user_agent = user_agents.get_user_agent_string()
        html_content = requests.get(page, proxies=proxies, headers={"User-Agent": user_agent}).content
        soup = BeautifulSoup(html_content, 'html.parser')

        images = soup.find_all("img")
        img_urls_to_contents = {}
        for image in images:
            img_url = image["src"]
            global_url = "".join(DeepCopyPage.globalize_url(page, img_url))
            contents = urllib.request.urlopen(global_url).read()
            image_contents = base64.b64encode(contents)
            img_urls_to_contents[img_url] = image_contents

        # Save all CSS files
        links = soup.find_all("link")
        link_urls_to_contents = {}
        for link in links:
            url = link["href"]
            global_url = "".join(DeepCopyPage.globalize_url(page, url))
            page_content = requests.get(global_url).content
            link_urls_to_contents[url] = page_content

        scripts = soup.find_all("script")
        script_urls_to_contents = {}
        for script in scripts:
            if script.has_attr("src"):
                url = script["src"]
                global_url = "".join(DeepCopyPage.globalize_url(page, url))
                page_content = requests.get(global_url).content
                link_urls_to_contents[url] = page_content

        print(link_urls_to_contents.keys())

        data_package.saved_pages = []
        data_package.saved_pages.append((page, html_content, img_urls_to_contents, link_urls_to_contents, script_urls_to_contents))


if __name__ == "__main__":

    copy_limb = DeepCopyPage({"SPOOF_USER_AGENT": True, "USE_PROXY_SERVER": True})
    pack = Package()
    copy_limb.scrape_from_url("http://boards.4channel.org/g/", pack)

    print(pack.saved_pages)