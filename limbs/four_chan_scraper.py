"""
four_chan_scraper.py - A Python module for Centipede that scrapes 4chan boards
"""

from centipede.limbs.abstract.Limb import Limb
from centipede import user_agents
from centipede import proxy_servers
from centipede import centipede_logger
from centipede.package import Package
from centipede.models.four_chan_thread import FourChanThread

import re
import requests
from datetime import datetime
import urllib.request
import base64
from bs4 import BeautifulSoup


class FourChanScraper(Limb):

    def __init__(self, config_dict):

        super(FourChanScraper, self).__init__(config_dict)

        self.uagent = None
        if config_dict.get("SPOOF_USER_AGENT", False):
            self.uagent = user_agents.get_user_agent_string()

        self.proxy_server = None
        if config_dict.get("USE_PROXY_SERVER", False):
            self.proxy_server = proxy_servers.pop()

        board_page_re = re.compile(".*4chan[nel]{0,3}\.org/./?$")
        self.associate_regex_with_method(board_page_re, self.parse_board_page)

        thread_page_re = re.compile(".*4chan[nel]{0,3}\.org/./thread/")
        self.associate_regex_with_method(thread_page_re, self.parse_thread_page)


    def parse_board_page(self, board_page, data_package):
        """
        Scrapes the front page of a 4chan board for the threads' data
        :param board_page: a URL from which to scrape data
        :param data_package: a Package object storing the threads' data
        :return: None
        """
        rand_proxy = proxy_servers.pop()
        proxies = {rand_proxy[2]: rand_proxy[0] + ":" + str(rand_proxy[1])}
        user_agent = user_agents.get_user_agent_string()
        html_content = requests.get(board_page, proxies=proxies, headers={"User-Agent": user_agent}).content
        soup = BeautifulSoup(html_content, 'html.parser')

        thread_objects = soup.select("div.thread")
        data_package.threads = []

        for thread_object in thread_objects:

            op_message_object = thread_object.select(".postContainer div.post blockquote.postMessage")[0]
            op_contents = op_message_object.decode_contents()
            op_contents = op_contents.replace("<br/>", "\n")

            op_date_object = thread_object.select(".postContainer div.post div.postInfo span.dateTime")[0]
            op_date = op_date_object.get_text()
            op_datetime = datetime.strptime(op_date, "%m/%d/%y(%a)%H:%M:%S")

            pinned = False
            pin_object = thread_object.find("img", class_="stickyIcon")
            if pin_object:
                pinned = True

            body_cut_off = False
            body_abbreviated_notice = thread_object.find("span", class_="abbr")
            if body_abbreviated_notice:
                body_cut_off = True

            abbreviated = False
            abbreviated_notice = thread_object.find("span", class_="summary")
            if abbreviated_notice:
                abbreviated = True

            image_contents = ""
            image_object = thread_object.find("a", class_="fileThumb")
            if image_object:
                image_href = image_object["href"]
                contents = urllib.request.urlopen("http:" + image_href).read()
                image_contents = base64.b64encode(contents)

            post_num_obj = thread_object.find("span", class_="postNum")
            post_num = post_num_obj.find_all("a")[1].get_text()

            if board_page.endswith("/"):
                thread_permalink = board_page + "thread/" + str(post_num)
            else:
                thread_permalink = board_page + "/thread/" + str(post_num)

            thread_attributes = {"is_pinned": pinned,
                                 "op_content": op_contents,
                                 "post_datetime": op_datetime,
                                 "image_content": image_contents,
                                 "abbreviated": abbreviated,
                                 "body_cut_off": body_cut_off,
                                 "post_num": post_num,
                                 "link": thread_permalink}
            thread_obj = FourChanThread(thread_attributes)

            data_package.threads.append(thread_obj)

        # Revisit any threads whose OPs are cut off, then revisit the front page of 4chan again
        data_package.linked_resources.extend([thread.link for thread in data_package.threads if thread.body_cut_off])
        data_package.linked_resources.append(board_page)
        data_package.html = html_content


    def parse_thread_page(self, thread_page, data_package):
        """
        Scrapes a specific page for a thread's information
        :param thread_page: the URL for a specific thread's page
        :param data_package: a Package instance storing the thread's data
        :return: None
        """
        rand_proxy = proxy_servers.pop()
        proxies = {rand_proxy[2]: rand_proxy[0] + ":" + str(rand_proxy[1])}
        user_agent = user_agents.get_user_agent_string()
        html_content = requests.get(thread_page, proxies=proxies, headers={"User-Agent": user_agent}).content
        soup = BeautifulSoup(html_content, 'html.parser')

        thread_object = soup.find_all("div", class_="thread")[0]

        op_content_obj = thread_object.select(".postContainer div.post blockquote.postMessage")[0]
        op_content = op_content_obj.decode_contents()
        op_content = op_content.replace("<br/>", "\n")

        op_date_object = thread_object.select(".postContainer div.post div.postInfo span.dateTime")[0]
        op_date = op_date_object.get_text()
        op_datetime = datetime.strptime(op_date, "%m/%d/%y(%a)%H:%M:%S")

        pinned = False
        pin_object = thread_object.find("img", class_="stickyIcon")
        if pin_object:
            pinned = True

        image_contents = ""
        image_object = thread_object.find("a", class_="fileThumb")
        if image_object:
            image_href = image_object["href"]
            contents = urllib.request.urlopen("http:" + image_href).read()
            image_contents = base64.b64encode(contents)

        post_num_obj = thread_object.find("span", class_="postNum")
        post_num = post_num_obj.find_all("a")[1].get_text()

        thread_permalink = thread_page + "thread/" + str(post_num)

        thread_attributes = {"is_pinned": pinned,
                             "op_content": op_content,
                             "post_datetime": op_datetime,
                             "image_content": image_contents,
                             "abbreviated": False,
                             "body_cut_off": False,
                             "post_num": post_num,
                             "link": thread_permalink}
        thread_obj = FourChanThread(thread_attributes)

        data_package.threads = []
        data_package.threads.append(thread_obj)


if __name__ == "__main__":
    scraper = FourChanScraper({"logger": centipede_logger})
    data_package = Package()
    # scraper.scrape_from_url("http://boards.4chan.org/a/", data_package)

    for thread in data_package.threads:
        print(thread)