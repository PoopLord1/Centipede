"""
YoutubeDownlaoderSeleniumScraper.py - a Limb that operates YoutubeDownloader.io in order to download a video. 
"""

import os, time, re

from .abstract.FirefoxSeleniumScraper import FirefoxSeleniumScraper


class YoutubeDownloader(FirefoxSeleniumScraper):

    def __init__(self, config_dict):
        super(YoutubeDownloader, self).__init__(config_dict)

        self.logger = config_dict["logger"].get_logger()

        video_page_re = re.compile(".*youtube\.com/watch")
        self.associate_regex_with_method(video_page_re, self.download_video)

    def download_video(self, video_page):
        """
        Download the video and save it to filesystem.
        """

        video_url = video_page.current_url
        video_id_match = self.video_id_re.search(video_url)
        video_id = None
        if video_id_match is not None:
            video_id = video_id_match.group(1)

        current_url = video_page.get_current_url()
        video_page.get(current_url.replace("youtube", "youtubepp"))
        dl_btn = video_page.find_element_by_xpath("//table/tbody/tr/td[3]/a")
        dl_btn.click()
        time.sleep(60)
        dl_btn2 = video_page.find_element_by_xpath("//div[@id='process-result']/div/a")
        dl_btn2.click()
        time.sleep(15)
        dl_obj = video_page.find_element_by_xpath("//div[@class='dlbtn']/a")
        dl_obj.click()

        # Wait for the file to finish downloading
        download_dir = "/download_dir"
        while True:
            files = os.listdir(download_dir)
            has_file_part = False
            for file in files:
                if file.endswith(".part"):
                    time.sleep(1)
                    has_file_part = True
            if not has_file_part:
                break

        newest_time = 0
        newest_file = ""
        for file in os.listdir(download_dir):
            mtime = os.path.getmtime(os.path.join(download_dir, file))
            if mtime > newest_time:
                newest_time = mtime
                newest_file = file
        os.rename(os.path.join(download_dir, newest_file), video_id + ".mp4")
        video_filepath = newest_file

        return video_filepath # TODO - figure out how to merge these things