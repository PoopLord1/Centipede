"""
Centipede.py - top-level framework that instantiates and calls the limbs in order.
"""

from centipede import resource_generator
from centipede import text_notification_manager
from centipede.package import Package
from centipede import centipede_logger
from centipede import limb_invocation_wrapper
from centipede import centipede_broker

import pickle
import multiprocessing


BROKER_PORT = 10000
LIMB_PORT_RANGE_START = 10001


class Centipede(object):
    def __init__(self, config=None):
        self.limb_classes = []
        self.limbs = []
        self.config = config

        self.limb_processes = []

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
            config_data = pickle.dumps(in_config)

            limb_port = LIMB_PORT_RANGE_START + i
            new_limb_process = multiprocessing.Process(target=limb_invocation_wrapper.create_limb, args=(limb, config_data, BROKER_PORT, limb_port))
            new_limb_process.start()
            self.limb_processes.append(new_limb_process)

            self.broker.associate_port_with_limb(limb_port, limb)


    @text_notification_manager.text_alert_on_exception
    def walk(self):
        for job in self.job_generator.iterate_pages():
            package = Package()

            if job:
                self.broker.put_data_in_pipeline(job.data_point)

            self.job_generator.add_to_queue(package.get_linked_resources())