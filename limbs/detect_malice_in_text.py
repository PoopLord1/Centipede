from twilio.rest import Client
import re
import flair

from centipede.limbs.abstract.Limb import Limb
from centipede.package import Package
from centipede.models.four_chan_thread import FourChanThread
from centipede.limbs import location_trie

from centipede.limbs.common.personal_information import twilio_constants
client = Client(twilio_constants.ACCOUNT_ID, twilio_constants.AUTH_TOKEN)


class DetectMaliceInText(Limb):
    """
    A class that analyzes text found in the data_package for malicious intent.
    """

    def __init__(self, config_dict):
        self.config_dict = config_dict

        super(DetectMaliceInText, self).__init__(config_dict)

        # self.flair_model = flair.models.TextClassifier.load('\\imdb-v0.4.pt')
        self.flair_model = None

        wildcard_re = re.compile("^")
        self.associate_regex_with_method(wildcard_re, self.analyze_for_malice)

        location_trie.add_from_school_listing()
        location_trie.add_from_us_cities()

    def analyze_for_malice(self, url, data_package):
        """
        Gathers and checks a segment of text for an intent commit terrorism
        :param url: the URL of the page being processed
        :param data_package: the Package() object containing the data accrued from previous limbs
        :return: None
        """

        print("Now in DetectMaliceInText.analyze_for_malice")

        get_text_method = self.config_dict.get("get_text_method", None)
        if get_text_method:
            text_segments = get_text_method(data_package)

            for i, text_segment in enumerate(text_segments):

                # s = flair.data.Sentence(text_segment)
                # self.flair_model.predict(s)
                # results_dict = s.labels[0].to_dict()
                # print(results_dict)

                is_malicious = False

                # Check to see if the text segment mentions a school
                if location_trie.contains_trie_contents(text_segment):
                    is_malicious = True

                data_package.threads[i].is_malicious = is_malicious

        else:
            raise AttributeError(
                "The config dict for " + self.__class__ + " must contain an attribute 'get_text_flag'.")


if __name__ == "__main__":
    config = {"get_text_method": lambda package: [ thread.op_content for thread in package.threads if not thread.body_cut_off ]}
    detect_malice_limb = DetectMaliceInText(config)

    package = Package()
    package.threads = [FourChanThread({"op_content": "I am literally going to kill everyone in Chicago tomorrow."})]

    detect_malice_limb.scrape_from_url("", package)