"""
RedditScraper.py - a Limb that scrapes data from a reddit page.
"""

from selenium.common.exceptions import NoSuchElementException

from centipede.limbs.abstract.ChromeSeleniumScraper import ChromeSeleniumScraper
from centipede.models.comment_data import CommentData
from centipede.internal.package import Package
from centipede.internal import centipede_logger
from centipede.models.reddit_post import RedditPost
from centipede.models.reddit_comment import RedditComment
from centipede.models.reddit_user import RedditUser

import re, time, base64, urllib, numpy, json, logging, random

NUMBER_POSTS_TO_SCRAPE = 30 # Scrape 30 posts on infinitely-loading pages, if that is not too much

GET_ID_FROM_COMMENTS_PAGE_RE = re.compile(".*reddit.com/r/.+/comments/([^/]+)")
UPVOTE_FORMAT_RE = re.compile("[\d.]+k?")


class RedditScraper(ChromeSeleniumScraper):

    def __init__(self, config_dict):
        self.config_dict = config_dict
        super(RedditScraper, self).__init__(config_dict)
        self.init_from_config(config_dict)

        self.subreddit_page_re = re.compile(".*reddit\.com/r/[^/]+/?$")
        self.associate_regex_with_method(self.subreddit_page_re, self.scrape_reddit_page)

        self.user_page_re = re.compile(".*reddit\.com/u")
        self.associate_regex_with_method(self.user_page_re, self.scrape_user_page)

        self.post_page_re = re.compile(".*reddit\.com/r/[^/]+/comments")
        self.associate_regex_with_method(self.post_page_re, self.scrape_post_page)


    def init_from_config(self, config_dict):
        self.logger = config_dict["logger"]


    def scrape_reddit_page(self, page_url, data_package):
        """
        Scrapes data found on a reddit page.
        """

        self.driver.get(page_url)
        self.logger.info("Now handling page " + page_url)

        wait_time = random.randrange(0, 8)
        time.sleep(wait_time)

        data_package.reddit_info = []

        posts = self.driver.find_elements_by_xpath("//body/div/div/div[2]/div[2]/div/div/div/div[2]/div[3]/div/div[4]/div") # assuming 1 based
        print("Length of posts: " + str(len(posts)))
        for i, post in enumerate(posts[:8]): # TODO - scroll down more to render more posts

            if not post.text:
                continue

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
                metadata_panel = post.find_element_by_xpath(".//div/div/div[2]/div[2]")
            else:
                metadata_panel = post.find_element_by_xpath(".//div/div/div[2]/div[1]")

            promoted = False
            try:
                promoted_obj = metadata_panel.find_element_by_xpath(".//div/div/span[1]")
                # print(promoted_obj.get_attribute("innerHTML"))
                promoted = promoted_obj.get_attribute("innerHTML").upper() == "PROMOTED"
            except:
                pass

            poster_name_obj = metadata_panel.find_element_by_xpath(".//div/div/div/a")
            print("Author: " + poster_name_obj.text)

            time_posted_obj = metadata_panel.find_element_by_xpath("./div/div/a")
            print("Time posted: " + time_posted_obj.text)

            print("Promoted: " + str(promoted))
            if promoted:
                title = "This was an ad; don't worry about the title"
            else:
                if pinned:
                    title_obj = post.find_element_by_xpath(".//div/div/div[2]/div[3]/div/a/div/h3")
                else:
                    title_obj = post.find_element_by_xpath(".//div/div/div[2]/div[2]/div/a/div/h3")
                title = title_obj.text
            print("Post title: " + title)

            if promoted:
                comments_link = "This was an ad; don't worry about the link for the reddit post"
            else:
                if pinned:
                    title_link_obj = post.find_element_by_xpath(".//div/div/div[2]/div[3]/div/a")
                else:
                    title_link_obj = post.find_element_by_xpath(".//div/div/div[2]/div[2]/div/a")
                comments_link = title_link_obj.get_attribute("href")
            print("Link to comments: " + comments_link)

            if promoted:
                content_link = "This was an ad; dont worry about the link to the article"
            else:
                try:
                    if pinned:
                        link_obj = post.find_element_by_xpath(".//div/div/div[2]/div[4]/a")
                    else:
                        link_obj = post.find_element_by_xpath(".//div/div/div[2]/div[3]/a")
                    content_link = link_obj.get_attribute("href")
                except NoSuchElementException:
                    content_link = comments_link
            print("Link to content: " + content_link)

            print()

            post_id = ""
            post_id_match = GET_ID_FROM_COMMENTS_PAGE_RE.search(comments_link)
            if post_id_match:
                post_id = post_id_match.group(1)

            if not promoted:
                post_data = RedditPost(input_dict={"post_id": post_id,
                                                   "points": score_obj.text,
                                                   "post_author": poster_name_obj.text,
                                                   "post_datetime": time_posted_obj.text,
                                                   "title": title_obj.text,
                                                   "comments_link": comments_link,
                                                   "content_link": content_link,
                                                   "source": page_url,
                                                   "rank": i})

                data_package.linked_resources.append(comments_link)
                data_package.linked_resources.append("http://www.reddit.com/u/" + poster_name_obj.text)

            data_package.reddit_info.append(post_data)


    def scrape_user_page(self, page_url, data_package):
        self.driver.get(page_url)
        self.logger.info("Now handling page " + page_url)

        wait_time = random.randrange(0, 8)
        time.sleep(wait_time)

        data_package.reddit_info = []

        username = None
        print(page_url)
        user_id_match = re.search("reddit\.com/user/([^/]+)/", page_url)
        if user_id_match:
            username = user_id_match.group(1)
        print(username)

        info_panel_obj = self.driver.find_element_by_xpath("//body/div/div/div[2]/div[2]/div/div/dIv/div[2]/div[4]/div[2]/div/div")
        # info_panel_obj = self.driver.find_element_by_xpath("//body/div/div/div[2]/div[2]/div/div/div")

        cake_day_object = info_panel_obj.find_element_by_xpath("./div/div[4]/div[2]/div/span")
        print(cake_day_object.text)
        cake_day_datetime = None

        total_karma_object = info_panel_obj.find_element_by_xpath("./div/div[4]/div/div/span")
        print(total_karma_object.text)

        data_package.reddit_info.append(RedditUser(input_dict={"user_id": username,
                                                               "total_karma": total_karma_object.text,
                                                               "cake_day_datetime": cake_day_datetime}))


        post_button_object = self.driver.find_element_by_xpath("//body/div/div/div[2]/div[2]/div/div/div/div[2]/div[2]/div/div/a[2]")
        post_button_object.click()
        wait_time = random.randrange(5, 15)
        time.sleep(wait_time)

        posts = self.driver.find_elements_by_xpath("//body/div/div/div[2]/div[2]/div/div/div/div[2]/div[4]/div/div[3]/div")
        for i, post in enumerate(posts):
            scoring_element = post.find_element_by_xpath(".//div/div/div")
            score_obj = scoring_element.find_element_by_xpath(".//div/div")
            print("Score: " + str(score_obj.text))

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
            if (span_obj_exists):  # and "pinned" in span_obj.get_attribute("innerHTML").lower()):
                pinned = True

            # TODO - look at pinned posts and learn to handle them
            # if pinned:
            #     # metadata_panel = post.find_element_by_xpath(".//div/div/div/div[2]/div[2]")
            # else:
            #     metadata_panel = post.find_element_by_xpath(".//div/div/div[2]/div[1]")

            # This is the tree for not pinned messages
            metadata_panel = post.find_element_by_xpath(".//div/div/div[2]/div/div[2]/div[2]/div[2]")

            promoted = False
            try:
                promoted_obj = metadata_panel.find_element_by_xpath("./div/div/span[1]")
                print(promoted_obj.get_attribute("innerHTML"))
                promoted = promoted_obj.get_attribute("innerHTML").upper() == "PROMOTED"
            except:
                pass

            time_posted_obj = metadata_panel.find_element_by_xpath("./a")
            print(time_posted_obj.text)

            print("Promoted: " + str(promoted))
            if promoted:
                title_obj = post.find_element_by_xpath(".//div/div/div[2]/div[2]/div/div/h3")
            else:
                title_obj = post.find_element_by_xpath(".//div/div/div[2]/div/div[2]/div/div/a/div/h3")
            print(title_obj.text)

            subreddit_obj = post.find_element_by_xpath(".//div/div/div[2]/div/div[2]/div[2]/div/a")
            print("Subreddit: " + subreddit_obj.text)

            if promoted:
                comments_link = "This was an ad; don't worry about the link for the reddit post"
            else:
                title_link_obj = post.find_element_by_xpath(".//div/div/div[2]/div/div[2]/div/div/a")
                comments_link = title_link_obj.get_attribute("href")
            print(comments_link)

            if promoted:
                content_link = "This was an ad; dont worry about the link to the article"
            else:
                link_obj = post.find_element_by_xpath(".//div/div/div[2]/div/div[2]/div/a")
                content_link = link_obj.get_attribute("href")
            print(content_link)

            print()

            post_data = RedditPost(input_dict={"post_id": "",
                                               "points": score_obj.text,
                                               "post_author": username,
                                               "post_datetime": time_posted_obj.text,
                                               "title": title_obj.text,
                                               "comments_link": comments_link,
                                               "content_link": content_link,
                                               "source": page_url,
                                               "rank": i})

            data_package.reddit_info.append(post_data)

            data_package.linked_resources.append(comments_link)

        comment_button_object = self.driver.find_element_by_xpath("//body/div/div/div[2]/div[2]/div/div/div/div[2]/div[2]/div/div/a[3]")
        comment_button_object.click()
        wait_time = random.randrange(5, 15)
        time.sleep(wait_time)

        comments = self.driver.find_elements_by_xpath("//body/div/div/div[2]/div[2]/div/div/div/div[2]/div[4]/div/div[3]/div/div")
        data_package.reddit_comments = []
        for i, comment in enumerate(comments):
            id_obj = comment.find_element_by_xpath("./div/div")
            id = id_obj.get_attribute("id")
            print(id)

            username_obj = comment.find_element_by_xpath("./div/div/div[2]/div[2]/div/div/a")
            username = username_obj.text
            print(username)

            flairs_and_points = comment.find_elements_by_xpath("./div/div/div[2]/div[2]/div/span")
            points_obj = flairs_and_points[-2]
            points = points_obj.get_attribute("innerHTML")
            print(points)

            time_obj = comment.find_element_by_xpath("./div/div/div[2]/div[2]/div/a/span")
            time_string = time_obj.get_attribute("innerHTML")
            print(time_string)

            body_obj = comment.find_element_by_xpath("./div/div/div[2]/div[2]/div[2]/div")
            body = body_obj.text
            print(body)

            comment_data = RedditComment(input_dict={"comment_id": id,
                                                     "content": body,
                                                     "comment_datetime": time_string,
                                                     "comment_author": username,
                                                     "points": points,
                                                     "source": page_url,
                                                     "rank": i})

            data_package.reddit_info.append(comment_data)

            # data_package.linked_resources.append() # TODO - append the post from which this comment was left

        print("done")



    def scrape_post_page(self, page_url, data_package):
        self.driver.get(page_url)
        self.logger.info("Now handling page " + page_url)

        wait_time = random.randrange(0, 8)
        time.sleep(wait_time)

        data_package.reddit_info = []

        # view_comments_button = self.driver.find_element_by_xpath("//body/div/div/div[2]/div[2]/div/div[3]/div/div[2]/div[4]/div/button")
        view_comments_button = None
        buttons = self.driver.find_elements_by_tag_name("button")
        for b in buttons:
            if b.text.upper().startswith("VIEW ENTIRE DISCUSSION"):
                view_comments_button = b
                break

        if view_comments_button:
            view_comments_button.click()

        # comments = self.driver.find_elements_by_xpath("//body/div/div/div[2]/div[2]/div/div/div/div[2]/div/div[2]/div[2]/div[4]/div/div/div/div") # 1-based
        comments = self.driver.find_elements_by_xpath("//body/div/div/div[2]/div[2]/div/div[3]/div/div[2]/div[6]/div/div/div/div")
        print(len(comments))


        for i, comment in enumerate(comments):

            # Sometimes, reddit provides a link to view deeper discussion on a new page
            # This shows up in a div just like any other comment. If we see this, skip it.
            continue_thread_obj = None
            try:
                continue_thread_obj = comment.find_element_by_xpath("./div/div/div[2]/a/span")
            except NoSuchElementException:
                pass

            if continue_thread_obj:
                continue

            # Reddit also shows deleted comments in a div just like regular comments, but without the data.
            # If we detect this, skip it.
            is_deleted_comment = False
            try:
                deleted_comment_text_obj = comment.find_element_by_xpath("./div/div/div[2]/div/div/span")
                if deleted_comment_text_obj.text.upper() == "COMMENT DELETED BY USER":
                    is_deleted_comment = True
            except NoSuchElementException:
                pass

            if is_deleted_comment:
                continue

            # Otherwise, grab all the comment data
            id_obj = comment.find_element_by_xpath("./div/div")
            id = id_obj.get_attribute("id")
            print(id)

            expand_button = None
            try:
                expand_button = comment.find_element_by_xpath("./div/div/div[2]/button")
            except NoSuchElementException:
                pass

            if expand_button:
                expand_button.click()

            username_obj = comment.find_element_by_xpath("./div/div/div[2]/div[2]/div/div/a")
            username = username_obj.text
            print(username)

            flairs_and_points = comment.find_elements_by_xpath("./div/div/div[2]/div[2]/div/span")
            points_obj = flairs_and_points[-2]
            points = points_obj.get_attribute("innerHTML")
            print(points)

            time_obj = comment.find_element_by_xpath("./div/div/div[2]/div[2]/div/a/span")
            time_string = time_obj.get_attribute("innerHTML")
            print(time_string)

            body_obj = comment.find_element_by_xpath("./div/div/div[2]/div[2]/div[2]/div")
            body = body_obj.text
            print(body)

            comment_data = RedditComment(input_dict={"comment_id": id,
                                                     "content": body,
                                                     "comment_datetime": time_string,
                                                     "comment_author": username,
                                                     "points": points,
                                                     "source": page_url,
                                                     "rank": i})

            data_package.reddit_info.append(comment_data)


if __name__ == "__main__":
    config_dict = {"logger": centipede_logger.create_logger("reddit_scraper", logging.DEBUG),
                   "ff_binary_location": "C:\\Program Files\\Mozilla Firefox",
                   "SPOOF_USER_AGENT": True,
                   "USE_PROXY_SERVER": False}
    scraper = RedditScraper(config_dict)

    pkg = Package()
    scraper.scrape_from_url("http://www.reddit.com/r/judo/", pkg)
    print(pkg.__dict__)
