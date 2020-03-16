"""
YoutubeScraper.py - a Limb that scrapes data from a Youtube channel or video.
"""

from centipede.limbs.abstract.ChromeSeleniumScraper import ChromeSeleniumScraper
from centipede.models.comment_data import CommentData

import re, time, base64, urllib, numpy, json


class YoutubeScraper(ChromeSeleniumScraper):

    def __init__(self, config_dict):
        super(YoutubeScraper, self).__init__(config_dict)
        self.init_from_config(config_dict)

        self.video_page_re = re.compile(".*youtube\.com/watch")
        self.associate_regex_with_method(self.video_page_re, self.scrape_video)

        self.channel_page_re = re.compile(".*youtube\.com/channel")
        self.associate_regex_with_method(self.channel_page_re, self.scrape_channel)

        self.user_page_re = re.compile(".*youtube\.com/user")
        self.associate_regex_with_method(self.user_page_re, self.scrape_channel)

    def init_from_config(self, config_dict):
        self.logger = config_dict["logger"].get_logger()

    def scrape_video(self, video_page, data_package):
        """
        Scrapes data found on a YouTube video page.
        Returns a VideoData instance.
        """
        time.sleep(10)
        video_title_obj = video_page.find_element_by_xpath("//div[@id='container']/h1/yt-formatted-string")
        video_title = video_title_obj.text

        video_url = video_page.current_url
        video_id_match = self.video_id_re.search(video_url)
        video_id = None
        if video_id_match is not None:
            video_id = video_id_match.group(1)

        upload_date_obj = video_page.find_element_by_xpath("//div[@id='upload-info']/span")
        upload_date_text = upload_date_obj.text
        upload_date_match = self.upload_date_re.search(upload_date_text)
        upload_date = None
        if upload_date_match:
            upload_date = upload_date_match.group(1)

        view_count_obj = video_page.find_element_by_xpath("//div[@id='count']/yt-view-count-renderer/span")
        view_count = view_count_obj.text

        likes_obj = video_page.find_element_by_xpath("//div[@id='top-level-buttons']/ytd-toggle-button-renderer/a/yt-formatted-string")
        num_likes = likes_obj.text

        dislikes_obj = video_page.find_element_by_xpath("//div[@id='top-level-buttons']/ytd-toggle-button-renderer[2]/a/yt-formatted-string")
        num_dislikes = dislikes_obj.text

        description_obj = video_page.find_element_by_xpath("//div[@id='description']/yt-formatted-string")
        description = description_obj.get_attribute("innerHTML")

        uploader_id = ""
        uploader_link_obj = video_page.find_element_by_xpath("//div[@id='owner-container']/yt-formatted-string/a")
        uploader_name = uploader_link_obj.text
        uploader_id_match = self.channel_id_re.search(uploader_link_obj.get_attribute("href"))
        if uploader_id_match:
            uploader_id = uploader_id_match.group(1)

        # Scroll to the bottom of the page, so the comments data can be rendered.
        video_page.execute_script("window.scrollTo(0, 520);")
        time.sleep(3)

        num_comments = -1
        num_comments_obj = video_page.find_element_by_xpath("//div[@id='title']/h2[@id='count']/yt-formatted-string")
        num_comments_match = self.num_comments_re.search(num_comments_obj.text)
        if num_comments_match:
            num_comments = num_comments_match.group(1)

        top_related_video_link_objs = video_page.find_elements_by_xpath("//ytd-compact-video-renderer[@class='style-scope ytd-watch-next-secondary-results-renderer']/div/div/a")
        top_related_video_link_objs = top_related_video_link_objs[:3]
        top_related_links = [link.get_attribute("href") for link in top_related_video_link_objs]

        thumbnail_url = "https://i.ytimg.com/vi/" + video_id + "/hqdefault.jpg"
        thumbnail_response = urllib.request.urlopen(thumbnail_url)
        thumbnail_base64_arr = numpy.asarray(bytearray(thumbnail_response.read()), dtype="uint8")
        thumbnail_base64 = base64.b64encode(thumbnail_base64_arr).decode("utf-8")

        comments = self.scrape_comments(video_page, video_id)

        self.logger.debug("video_title: " + video_title)
        self.logger.debug("num_likes: " + num_likes)
        self.logger.debug("num_dislikes: " + num_dislikes)
        self.logger.debug("description: " + description)
        self.logger.debug("video_id: " + video_id)
        self.logger.debug("upload_date: " + upload_date)
        self.logger.debug("view_count: " + view_count)
        self.logger.debug("uploader_name: " + uploader_name)
        self.logger.debug("uploader_id: " + uploader_id)
        self.logger.debug("num_comments: " + num_comments)
        self.logger.debug("top related videos: " + json.dumps(top_related_links))

        data_package.add_attributes(input_dict={
            "title": video_title,
            "id": video_id,
            "upload_date": upload_date,
            "views": view_count,
            "likes": num_likes,
            "dislikes": num_dislikes,
            "description": description,
            "comments": comments,
            "channel_id": uploader_id,
            "num_comments": num_comments,
            "top_related_videos": top_related_links,
            "thumbnail": thumbnail_base64,
            "video_filepath": ""
        })

    def scrape_channel(self, channel_page, data_package):
        """
        Gather channel-related data, given that we have navigated to that channel already.
        Returns a ChannelData instance.
        """
        time.sleep(20)
        channel_name_obj = channel_page.find_element_by_xpath("//h1[@id='channel-title-container']/span")
        channel_name = channel_name_obj.text

        channel_id_match = self.channel_id_re.search(channel_page.current_url)
        channel_id = ""
        if channel_id_match:
            channel_id = channel_id_match.group(1)

        subscribers_obj = channel_page.find_element_by_xpath("//div[@id='inner-header-container']/yt-formatted-string")
        num_subscribers_text = subscribers_obj.text
        subscribers_match = self.num_subscribers_re.search(num_subscribers_text)
        num_subscribers = -1
        if subscribers_match:
            num_subscribers = int(subscribers_match.group(1).replace(",", ""))

        sidebar_category_objs = channel_page.find_elements_by_xpath("//div[@id='secondary']/ytd-browse-secondary-contents-renderer/div[@id='contents']/ytd-vertical-channel-section-renderer")
        related_channels_obj = None
        for sidebar_category_obj in sidebar_category_objs:
            if sidebar_category_obj.find_element_by_xpath(".//h2[@id='title']").text.strip().lower() == "related channels":
                related_channels_obj = sidebar_category_obj


        related_channels = []
        if related_channels_obj:
            related_channel_links = related_channels_obj.find_elements_by_xpath(".//div[@id='items']/ytd-mini-channel-renderer/a")
            for related_channel_link in related_channel_links:
                related_channels.append(related_channel_link.get_attribute("href"))

        # Change to the "About" tab
        about_tab_obj = channel_page.find_elements_by_xpath("//paper-tabs[@id='tabs']/div/div/paper-tab")[-2]
        # about_tab = about_tab_obj.find_element_by_xpath(".//paper-ripple")
        about_tab_obj.click()
        time.sleep(2)

        join_date_obj = channel_page.find_element_by_xpath("//div[@id='right-column']/yt-formatted-string[2]")
        join_date_match = self.join_date_re.search(join_date_obj.text)
        if join_date_match:
            join_date = join_date_match.group(1)

        channel_views_obj = channel_page.find_element_by_xpath("//div[@id='right-column']/yt-formatted-string[3]")
        channel_views_match = self.channel_views_re.search(channel_views_obj.text)
        if channel_views_match:
            channel_views = channel_views_match.group(1)

        description_object = channel_page.find_element_by_xpath("//div[@id='description-container']/yt-formatted-string[2]")
        description = description_object.text

        # Now move to "Videos" tab and keep scrolling to the bottom.
        about_tab_obj = channel_page.find_element_by_xpath("//paper-tabs[@id='tabs']/div/div/paper-tab[2]")
        about_tab_obj.click()
        time.sleep(4)

        last_height = channel_page.execute_script("return document.body.scrollHeight")
        new_height = -1
        while new_height != last_height:
            channel_page.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(3)
            last_height = new_height
            new_height = channel_page.execute_script("return document.documentElement.scrollHeight;")

        video_container_objs = channel_page.find_elements_by_xpath("//div[@id='contents']/ytd-grid-renderer/div/ytd-grid-video-renderer")
        video_ids = []
        for video_container_obj in video_container_objs:
            link_obj = video_container_obj.find_element_by_xpath(".//div/ytd-thumbnail/a")
            video_ids.append(link_obj.get_attribute("href"))

        self.logger.debug("Channel data:")
        self.logger.debug("Channel Name: " + channel_name)
        self.logger.debug("Channel id: " + channel_id)
        self.logger.debug("Num Subscribers: " + str(num_subscribers))
        self.logger.debug("Join date: " + join_date)
        self.logger.debug("Channel views: " + channel_views)
        self.logger.debug("Channel Description: " + description)
        self.logger.debug("Number of total videos: " + str(len(video_ids)))

        data_package.add_attributes(input_dict={"name": channel_name,
                                              "url": channel_id,
                                              "num_subscribers": num_subscribers,
                                              "associated_channels": related_channels,
                                              "join_date": join_date,
                                              "channel_views": channel_views,
                                              "description": description,
                                              "all_video_ids": video_ids})


    def scrape_comments(self, driver, video_id):
        """
        Scrapes data pertaining to the first few comments on a video page.
        Returns an array of CommentData instances.
        """
        comment_objs = driver.find_elements_by_xpath("//div[@id='contents']/ytd-comment-thread-renderer")
        comments = []
        for comment_obj in comment_objs:
            comment_body = comment_obj.find_element_by_xpath("ytd-comment-renderer/div[2]/div[2]/ytd-expander/div/yt-formatted-string[2]").text

            comment_author_link_obj = comment_obj.find_element_by_xpath("ytd-comment-renderer/div[2]/div[2]/div/div[@id='header-author']/a")
            comment_author_link = comment_author_link_obj.get_attribute("href")

            comment_author = comment_author_link_obj.find_element_by_xpath("span").text.strip()

            comment_score = comment_obj.find_element_by_xpath("ytd-comment-renderer/div[2]/div[2]/ytd-comment-action-buttons-renderer/div/span[2]").text.strip()

            comment_date = comment_obj.find_element_by_xpath("ytd-comment-renderer/div[2]/div[2]/div[@id='header']/div[2]/yt-formatted-string/a").text

            comment_instance = CommentData(input_dict={"video_url": video_id,
                                                       "body": comment_body,
                                                       "commenter": comment_author,
                                                       "commenter_id": comment_author_link,
                                                       "comment_date": comment_date,
                                                       "score": comment_score})
            comments.append(comment_instance)

        return comments

