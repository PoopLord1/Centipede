"""
RedditScraper.py - a Limb that scrapes data from a reddit page.
"""

from centipede.limbs.abstract.ChromeSeleniumScraper import ChromeSeleniumScraper
from centipede.models.comment_data import CommentData
from centipede.internal.package import Package
from centipede.internal import centipede_logger

import re, time, base64, urllib, numpy, json, logging, random

UPVOTE_FORMAT_RE = re.compile("[\d.]+k?")

class RedditScraper(ChromeSeleniumScraper):

    def __init__(self, config_dict):
        self.config_dict = config_dict
        super(RedditScraper, self).__init__(config_dict)
        self.init_from_config(config_dict)

        self.subreddit_page_re = re.compile(".*reddit\.com/r/[^/]+/?$")
        self.associate_regex_with_method(self.subreddit_page_re, self.scrape_reddit_page)

        self.user_page_re = re.compile(".*reddit\.com/u")
        # self.associate_regex_with_method(self.user_page_re, self.scrape_user_page)

        self.post_page_re = re.compile(".*reddit\.com/[^/]+/comments")
        # self.associate_regex_with_method(self.post_page_re, self.scrape_post_page)


    def init_from_config(self, config_dict):
        self.logger = config_dict["logger"]


    def scrape_reddit_page(self, page_url, data_package):
        """
        Scrapes data found on a reddit page.
        """

        self.driver.get(page_url)
        self.logger.info("Now handling page " + page_url)

        wait_time = random.randrange(5, 15)
        time.sleep(wait_time)

        # Get one post

        posts = self.driver.find_elements_by_xpath("//body/div/div/div[2]/div[2]/div/div/div/div[2]/div[3]/div/div[4]/div") # assuming 1 based
        print("Length of posts: " + str(len(posts)))
        for post in posts[:8]: # TODO - scroll down more to render more posts

            scoring_element = post.find_element_by_xpath(".//div/div/div[1]")
            score_obj = scoring_element.find_element_by_xpath(".//div/div")
            print(score_obj.text)

            first_text_in_post = post.find_element_by_xpath(".//div/div/div[2]/div[1]")
            span_obj = None
            span_obj_exists = False
            try:
                span_obj = first_text_in_post.find_element_by_xpath("./span")
                span_obj_exists = True
            except:
                pass

            pinned = False
            print(span_obj_exists)
            # print(span_obj.get_attribute("innerHTML"))
            if (span_obj_exists): #  and "pinned" in span_obj.get_attribute("innerHTML").lower()):
                pinned = True

            if pinned:
                metadata_panel = post.find_element_by_xpath(".//div/div/div/div[2]/div[2]")
            else:
                metadata_panel = post.find_element_by_xpath(".//div/div/div[2]/div[1]")

            promoted = False
            try:
                promoted_obj = metadata_panel.find_element_by_xpath("./div/div/span[1]")
                print(promoted_obj.get_attribute("innerHTML"))
                promoted = promoted_obj.get_attribute("innerHTML").upper() == "PROMOTED"
            except:
                pass

            poster_name_obj = metadata_panel.find_element_by_xpath("./div/div/div/a")
            print(poster_name_obj.text)

            time_posted_obj = metadata_panel.find_element_by_xpath("./div/div/a")
            print(time_posted_obj.text)

            print("Promoted: " + str(promoted))
            if promoted:
                title_obj = post.find_element_by_xpath("./div/div/div[2]/div[2]/div/div/h3")
            else:
                title_obj = post.find_element_by_xpath("./div/div/div[2]/div[2]/div/a/div/h3")
            print(title_obj.text)

            if promoted:
                title_link = "This was an ad; don't worry about the link for the reddit post"
            else:
                title_link_obj = post.find_element_by_xpath(".//div/div/div[2]/div[2]/div/a")
                title_link = title_link_obj.get_attribute("href")
            print(title_link)

            if promoted:
                link = "This was an ad; dont worry about the link to the article"
            else:
                link_obj = post.find_element_by_xpath("./div/div/div[2]/div[3]/a")
                link = link_obj.get_attribute("href")
            print(link)

            print()




if __name__ == "__main__":
    config_dict = {"logger": centipede_logger.create_logger("reddit_scraper", logging.DEBUG),
                   "ff_binary_location": "C:\\Program Files\\Mozilla Firefox",
                   "SPOOF_USER_AGENT": True,
                   "USE_PROXY_SERVER": False}
    scraper = RedditScraper(config_dict)

    pkg = Package()
    scraper.scrape_from_url("https://www.reddit.com/r/videos/", pkg)
    print(pkg.__dict__)