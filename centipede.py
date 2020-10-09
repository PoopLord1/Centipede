"""
Centipede.py - top-level framework that instantiates and calls the limbs in order.
"""

#from centipede import text_notification_manager
from centipede.internal.package import Package
from centipede.internal import centipede_broker, centipede_logger, resource_generator

import threading

PERIODIC_LINKED_RESOURCES_DELAY = 1


class Centipede(object):
    def __init__(self, config=None):
        self.limb_classes = []
        self.limbs = []
        self.config = config

        common_config = self.config.GENERAL
        specific_config = getattr(self.config, "UrlGenerator")
        gen_config = {**common_config, **specific_config}
        self.job_generator = resource_generator.UrlGenerator(config=gen_config)

        self.log_level = self.config.GENERAL["log_level"]
        self.logger = centipede_logger.create_logger(self.__class__.__name__, self.log_level)

        self.broker = centipede_broker.CentipedeBroker()

        threading.Timer(0, self.update_linked_resources).start()


    def define_limbs(self, limb_classes):
        self.limb_classes = limb_classes
        self.broker.set_limb_pipeline(self.limb_classes)
        common_config = self.config.GENERAL
        for i, limb in enumerate(self.limb_classes):
            class_name = str(limb.__name__)
            specific_config = getattr(self.config, class_name)

            in_config = {**common_config, **specific_config}
            self.broker.save_limb_config(limb, in_config)
            self.broker.create_process(limb.__name__)


    def update_linked_resources(self):
        self.job_generator.add_to_queue(self.broker.grab_linked_resources())
        threading.Timer(PERIODIC_LINKED_RESOURCES_DELAY, self.update_linked_resources).start()


    # @text_notification_manager.text_alert_on_exception
    def walk(self):
        for job in self.job_generator.iterate_pages():
            if job:
                self.broker.put_data_in_pipeline(job.data_point)