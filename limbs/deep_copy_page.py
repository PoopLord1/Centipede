"""
deep_copy_page.py - A Limb that accepts
"""

import re
import requests
import urllib
import base64
from bs4 import BeautifulSoup
import os
import uuid
import time

from centipede.limbs.abstract.Limb import Limb
from centipede import user_agents
from centipede import proxy_servers
from centipede.package import Package

class DeepCopyPage(Limb):

    url_re = re.compile("([^/]+)?:?(//)?([^/]+)?([^$]*)")

    IMAGE_EXTENSIONS = ["JPG", "JPEG", "PNG", "GIF", "BMP", "TIF", "TGA"]

    def __init__(self, config_dict):

        self.config_dict = config_dict

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

        time_start = time.time()
        rand_proxy = proxy_servers.pop()
        proxies = {rand_proxy[2]: rand_proxy[0] + ":" + str(rand_proxy[1])}
        user_agent = user_agents.get_user_agent_string()
        html_content = requests.get(page, proxies=proxies, headers={"User-Agent": user_agent}).content
        html_string = html_content.decode("utf-8")
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

        # Save all images directly linked from this page
        anchors = soup.find_all("a")
        img_links_to_contents = {}
        for anchor in anchors:
            href = anchor["href"]
            last_question_mark = href.rfind("?")
            if last_question_mark != -1:
                href_no_params = href[:last_question_mark+1]
            else:
                href_no_params = href

            last_dot_i = href_no_params.rfind(".")
            ext = href_no_params[last_dot_i+1:]

            if ext.upper() in DeepCopyPage.IMAGE_EXTENSIONS:
                global_url = "".join(DeepCopyPage.globalize_url(page, href_no_params))
                page_content = requests.get(global_url).content
                img_links_to_contents[href] = page_content


        data_package.saved_pages = []
        data_package.saved_pages.append((page, html_content, img_urls_to_contents, link_urls_to_contents, script_urls_to_contents))

        # Create a folder, and then files for each of the linked resources
        escaped_url = page.replace("/", "_").replace(":", "_")
        saved_pages_root = ""
        resource_folder = os.path.join(saved_pages_root, escaped_url)
        os.mkdir(resource_folder)

        for img_url in img_urls_to_contents:
            uid = uuid.uuid4().hex
            contents = img_urls_to_contents[img_url]

            params_start_i = img_url.find("?")
            if params_start_i != -1:
                img_url = img_url[:params_start_i]
            last_dot_i = img_url.rfind(".")
            last_slash_i = img_url.rfind("/")
            if last_dot_i > last_slash_i:
                ext = img_url[last_dot_i+1:]

                fp = open(resource_folder + "\\" + uid + "." + ext, "wb+")
                fp.write(base64.decodebytes(contents))
                fp.close()

                html_string = html_string.replace(img_url, resource_folder + "\\" + uid + "." + ext)

        for link_url in link_urls_to_contents:
            uid = uuid.uuid4().hex
            contents = link_urls_to_contents[link_url]

            params_start_i = link_url.find("?")
            if params_start_i != -1:
                link_url = link_url[:params_start_i]
            last_dot_i = link_url.rfind(".")
            last_slash_i = link_url.rfind("/")
            if last_dot_i > last_slash_i:
                ext = link_url[last_dot_i + 1:]

                fp = open(resource_folder + "\\" + uid + "." + ext, "wb+")
                fp.write(contents)
                fp.close()

                html_string = html_string.replace(link_url, resource_folder + "\\" + uid + "." + ext)

        for script_url in script_urls_to_contents:
            uid = uuid.uuid4().hex
            contents = script_urls_to_contents[script_url]

            params_start_i = script_url.find("?")
            if params_start_i != -1:
                script_url = script_url[:params_start_i]
            last_dot_i = script_url.rfind(".")
            last_slash_i = script_url.rfind("/")
            if last_dot_i > last_slash_i:
                ext = script_url[last_dot_i + 1:]

                fp = open(resource_folder + "\\" + uid + "." + ext, "wb+")
                fp.write(contents)
                fp.close()

                html_string = html_string.replace(script_url, resource_folder + "\\" + uid + "." + ext)

        # Save all images that are directly linked from this page
        for img_link in img_links_to_contents:
            uid = uuid.uuid4().hex
            contents = img_links_to_contents[img_link]

            params_start_i = img_link.find("?")
            if params_start_i != -1:
                img_link = img_link[:params_start_i]
            last_dot_i = img_link.rfind(".")
            last_slash_i = img_link.rfind("/")
            if last_dot_i > last_slash_i:
                ext = img_link[last_dot_i + 1:]

                fp = open(resource_folder + "\\" + uid + "." + ext, "wb+")
                fp.write(contents)
                fp.close()

                html_string = html_string.replace(img_link, resource_folder + "\\" + uid + "." + ext)

        # Save page data
        fp = open(resource_folder + "\\html.html", "wb")
        fp.write(html_string.encode("utf-8"))
        fp.close()

        time_end = time.time()

if __name__ == "__main__":

    copy_limb = DeepCopyPage({"SPOOF_USER_AGENT": True, "USE_PROXY_SERVER": True})
    pack = Package()
    copy_limb.scrape_from_url("http://boards.4channel.org/g/", pack)

    print(pack.saved_pages)