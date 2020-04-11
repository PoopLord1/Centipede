import threading
import pickle
import multiprocessing
import uuid

from collections import deque

from centipede.internal.package import Package
from centipede.internal.broker_communicator import BrokerCommunicator, BROKER_PORT
from centipede.internal import limb_invocation_wrapper
from centipede.internal.limb_timing_manager import TimingManager


class SupportBroker(object):

    master_ip = ""

    def __init__(self, master_ip):
        self.master_ip = master_ip