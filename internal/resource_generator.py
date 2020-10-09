
import logging

from centipede.internal import centipede_logger, ingestion_queue_manager


class UrlGenerator(object):

    def __init__(self, config=None):
        self.resource_queue = ingestion_queue_manager.IngestionQueueManager(config)

        self.logger = centipede_logger.create_logger(self.__class__.__name__, logging.DEBUG)


    def iterate_pages(self):
        while True:
            # Pop thing off of IngestionQueue
            resource_url = self.resource_queue.next_resource()

            yield resource_url


    def add_to_queue(self, resources):
        self.resource_queue.push_resources(resources)
