from twilio.rest import Client
import re
import logging
import time

from centipede.limbs.abstract.Limb import Limb
from centipede.internal.package import Package

from centipede.limbs.common.personal_information import twilio_constants
from centipede.internal import centipede_logger

client = Client(twilio_constants.ACCOUNT_ID, twilio_constants.AUTH_TOKEN)


class SleepLimb(Limb):
    """
    A class that sends a text to a pre-defined number when certain configurable conditions are met.
    """

    def __init__(self, config_dict):
        self.config_dict = config_dict

        super(SleepLimb, self).__init__(config_dict)

        self.logger = config_dict["logger"]

        wildcard_re = re.compile("^")
        self.associate_regex_with_method(wildcard_re, self.ingest)

    def ingest(self, url, data_package):
        """
        Sends a text message to a pre-defined number based on attributes of data_package
        :param url: the URL of the page being processed
        :param data_package: the Package() object containing the data accrued from previous limbs
        :return: None
        """

        self.logger.info("Currently processing " + url + " with the sleep limb. No action has been taken.")
        time.sleep(5)
        self.logger.info("\t Done.")


if __name__ == "__main__":
    config = {"logger": centipede_logger.create_logger("empty_limb", logging.DEBUG)}
    send_text = SleepLimb(config)

    pack = Package()
    send_text.scrape_from_url("", pack)
