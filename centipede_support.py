
from centipede.internal.support_broker import SupportBroker

class CentipedeSupport(object):

    def __init__(self, master_ip):

        self.support_broker = SupportBroker(master_ip)

    def support(self):
        self.support_broker.start_support()