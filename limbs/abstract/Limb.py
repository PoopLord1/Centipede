"""
An abstract class that defines the requirements for any "limb," or individual scraping module.
"""

from abc import ABC, abstractmethod
import re

class Limb(ABC):

	# Associates a compiled regex object to a scraping method.
	_COMPILED_RE_TYPE = type(re.compile(""))


	def __init__(self, config_dict):
		self.regex_to_scraping_method = {}
		self.init_from_config(config_dict)
		super(Limb, self).__init__()

	def init_from_config(self, config_dict):
		pass

	def scrape_from_url(self, url, prior_data):
		"""
		Given a url string, ingests information from that URL.
		Branches into different methods depending on structure of URL.
		Returns a dictionry of information scraped / determined.
		"""
		for regex in self.regex_to_scraping_method:
			match = regex.match(url)
			if match:
				scraping_method = self.regex_to_scraping_method[regex]
				scraping_method(url, prior_data)

		return prior_data


	def associate_regex_with_method(self, regex, method):
		"""
		Internally associates a regular expression with a scraping method.
		When a url is meant to be scraped, if it matches this regex, this method is called.
		"""
		if isinstance(regex, Limb._COMPILED_RE_TYPE):
			self.regex_to_scraping_method[regex] = method
		else:
			compiled_regex = re.compile(regex)
			self.regex_to_scraping_method[compiled_regex] = method

