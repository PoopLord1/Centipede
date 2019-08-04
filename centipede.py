"""
ScrapeElsagate.py - the top-level code that governs the Elsagate pattern of web scraping.
"""

import sys
import re
import logging
import os

from centipede import resource_generator
from centipede import text_notification_manager
from centipede.package import Package

# TODO - implement a queue for the urls to be processed
# TODO - implement the ability to artificially add new urls to the queue, if they weren't in there before


class Centipede(object):
    def __init__(self, config=None):
        self.limb_classes = []
        self.limbs = []
        self.config = config

        common_config = self.config.GENERAL
        specific_config = getattr(self.config, "UrlGenerator")
        gen_config = {**common_config, **specific_config}
        self.page_generator = resource_generator.UrlGenerator(config=gen_config)

    def define_limbs(self, limb_classes):
        self.limb_classes = limb_classes
        common_config = self.config.GENERAL
        print(self.limb_classes)
        for limb in self.limb_classes:
            print(limb)
            class_name = str(limb.__name__)
            print(class_name)
            sys.stdout.flush()
            specific_config = getattr(self.config, class_name)
            in_config = {**common_config, **specific_config}
            self.limbs.append(limb(in_config))

    @text_notification_manager.text_alert_on_exception
    def walk(self):
        for page in self.page_generator.iterate_pages():
            package = Package()

            for limb in self.limbs:
                package = limb.scrape_from_url(page, package)

            self.page_generator.add_to_queue(package.get_linked_resources())
