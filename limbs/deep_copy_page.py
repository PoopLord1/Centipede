"""
deep_copy_page.py - A Limb that accepts any URL as input through Centipede framework, and deeply copies it to disk.
"""

import re
import requests
from bs4 import BeautifulSoup
import os
import uuid
import time
import threading
import logging
from datetime import datetime

from limbs.abstract.Limb import Limb
import user_agents
import proxy_servers
from package import Package
import centipede_logger


class DeepCopyPage(Limb):

    url_re = re.compile("([^/]+)?:?(//)?([^/]+)?([^$]*)")

    FILETYPES_TO_COPY = ["JPG", "JPEG", "PNG", "GIF", "BMP", "TIF", "JS", "CSS", "MP4", "WEBM", "MPEG", "ICO", "RSS"]

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

        self.logger = self.config_dict["logger"]

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

        return "".join(global_tokens)

    def save_single_resource(self, url, uid, base_dir, ext):
        contents = requests.get(url).content

        fp = open(base_dir + "\\" + uid + "." + ext, "wb+")
        fp.write(contents)
        fp.close()

    def deep_copy_page(self, page, data_package):

        start_time = time.time()
        self.logger.info("Now processing " + page)

        should_copy_page = True
        is_conditional_copy = self.config_dict.get("is_conditional", False)
        if is_conditional_copy:
            has_should_copy_flag = "should_copy_flag" in self.config_dict
            if has_should_copy_flag:
                should_copy_func = self.config_dict["should_copy_flag"]

                try:
                    should_copy_page = should_copy_func(data_package)
                except Exception as e:
                    self.config_dict["logger"].error("Unable to run DeepCopyPage's should_copy_flag with the current data package.")
                    self.config_dict["logger"].error(str(e))
                    should_copy_page = False

            else:
                raise AttributeError("The config for DeepCopyPage shows that we should only copy the page under " +
                                     "certain conditions, but does not define those conditions. Add a function " +
                                     "definition under the config key \'should_copy_flag\'")

        if should_copy_page:
            data_package.saved_pages = []

            escaped_url = re.sub(".*?://", "", page)
            escaped_url = escaped_url.replace("/", "_").replace(":", "_")
            now = datetime.now()
            escaped_url += "_" + now.strftime("%Y%m%d_%H%M%S")

            # Create a folder to hold all of our resources
            saved_pages_root = "saved_pages"
            resource_folder = os.path.join(saved_pages_root, escaped_url)
            os.makedirs(resource_folder)

            # Grab the raw html and parse it
            if hasattr(data_package, "html") and data_package.html:
                html_content = data_package.html
            else:
                proxies = {self.proxy_server[2]: self.proxy_server[0] + ":" + str(self.proxy_server[1])}
                header = {"User-Agent": self.uagent,
                          "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                          "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.3",
                          "Accept-Encoding": "none",
                          "Accept-Language": "en-US,en;q=0.8",
                          "Connection": "keep-alive"}
                html_content = requests.get(page, proxies=proxies, headers=header).content
            html_string = html_content.decode("utf-8")
            soup = BeautifulSoup(html_content, 'html.parser')

            # We will be analyzing resources linked from img, link, script, and a tags.
            # (relevant file extensions can be found in DeepCopyLimb.FILETYPES_TO_COPY)
            objects_to_copy = []
            objects_to_copy.extend(soup.find_all("img"))
            objects_to_copy.extend(soup.find_all("link"))
            objects_to_copy.extend(soup.find_all("script"))
            objects_to_copy.extend(soup.find_all("a"))

            saving_threads = []

            saved_urls = set()
            for obj in objects_to_copy:
                tag_type = obj.name

                rel_url = ""
                if tag_type == "img":
                    rel_url = obj["src"]
                elif tag_type == "link":
                    rel_url = obj["href"]
                elif tag_type == "script":
                    if obj.has_attr("src"):
                        rel_url = obj["src"]
                elif tag_type == "a":
                    rel_url = obj["href"]

                if rel_url and rel_url not in saved_urls:
                    global_url = DeepCopyPage.globalize_url(page, rel_url)

                    # Grab the file extension
                    params_start_i = global_url.find("?")
                    if params_start_i != -1:
                        global_url = global_url[:params_start_i]
                    last_dot_i = global_url.rfind(".")
                    last_slash_i = global_url.rfind("/")
                    if last_dot_i > last_slash_i:
                        ext = global_url[last_dot_i + 1:]

                        # If the file extension is relevant to us, save it in a new file
                        if ext.upper() in DeepCopyPage.FILETYPES_TO_COPY:
                            uid = uuid.uuid4().hex

                            saving_thread = threading.Thread(target=self.save_single_resource, args=(global_url, uid, resource_folder, ext))
                            saving_threads.append(saving_thread)
                            saving_thread.start()

                            saved_urls.add(rel_url)

                            # And update the original html to point to our saved resource
                            html_string = html_string.replace(rel_url, uid + "." + ext)
                            data_package.saved_pages.append(global_url)

            for saving_thread in saving_threads:
                saving_thread.join()

            # Finally, save the modified HTML that points to our resources
            fp = open(resource_folder + "\\html.html", "wb")
            fp.write(html_string.encode("utf-8"))
            fp.close()

        if should_copy_page:
            self.logger.debug("Just finished copying " + page + " in " + str(time.time() - start_time) + " seconds.")
        else:
            self.logger.debug(page + " was not malicious, so we did not copy it.")


if __name__ == "__main__":

    centipede_logger.init(logging.DEBUG)
    copy_limb = DeepCopyPage({"SPOOF_USER_AGENT": True, "USE_PROXY_SERVER": True, "logger": centipede_logger.get_logger()})
    pack = Package()

    start_time = time.time()
    copy_limb.scrape_from_url("http://boards.4channel.org/g/", pack)
    print("Time taken: " + str(time.time() - start_time))

    print(pack.saved_pages)