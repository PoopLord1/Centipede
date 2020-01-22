"""
Centipede.py - top-level framework that instantiates and calls the limbs in order.
"""

from centipede import resource_generator
from centipede import text_notification_manager
from centipede.package import Package
from centipede import centipede_broker


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

        self.broker = centipede_broker.CentipedeBroker()


    def define_limbs(self, limb_classes):
        self.limb_classes = limb_classes
        self.broker.set_limb_pipeline(limb_classes)
        common_config = self.config.GENERAL
        for i, limb in enumerate(self.limb_classes):
            class_name = str(limb.__name__)
            specific_config = getattr(self.config, class_name)

            in_config = {**common_config, **specific_config}
            self.broker.create_limb(limb, in_config)


    @text_notification_manager.text_alert_on_exception
    def walk(self):
        for job in self.job_generator.iterate_pages():
            package = Package()

            if job:
                self.broker.put_data_in_pipeline(job.data_point)

            self.job_generator.add_to_queue(package.get_linked_resources())