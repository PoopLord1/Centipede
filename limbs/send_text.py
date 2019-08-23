from twilio.rest import Client
import re

from centipede.limbs.abstract.Limb import Limb
from centipede.package import Package

from centipede.limbs.common.personal_information import twilio_constants
client = Client(twilio_constants.ACCOUNT_ID, twilio_constants.AUTH_TOKEN)


class SendText(Limb):
    """
    A class that sends a text to a pre-defined number when certain configurable conditions are met.
    """

    def __init__(self, config_dict):
        self.config_dict = config_dict

        super(SendText, self).__init__(config_dict)

        wildcard_re = re.compile("^")
        self.associate_regex_with_method(wildcard_re, self.send_text)

    def send_text(self, url, data_package):
        """
        Sends a text message to a pre-defined number based on attributes of data_package
        :param url: the URL of the page being processed
        :param data_package: the Package() object containing the data accrued from previous limbs
        :return: None
        """
        get_send_flag_func = self.config_dict.get("get_text_flag")
        if get_send_flag_func:

            send_text_flag = False
            try:
                send_text_flag = get_send_flag_func(data_package)
            except:
                pass

            if send_text_flag:

                message_body = self.config_dict["message_template"].format(url)
                message_params = {"body": "-\n\n" + message_body,
                                  "from_": twilio_constants.TWILIO_NUMBER,
                                  "to": twilio_constants.DEST_NUMBER}
                client.messages.create(**message_params)


if __name__ == "__main__":
    config = {"get_text_flag": lambda package: package.is_malicious,
              "message_template": "The thread found at {} was found to be malicious!"}
    send_text = SendText(config)

    pack = Package()
    pack.is_malicious = True
    send_text.scrape_from_url("", pack)
