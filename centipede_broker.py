import threading
import pickle
import multiprocessing

from collections import deque

from centipede.package import Package
from centipede.broker_communicator import BrokerCommunicator, BROKER_PORT
from centipede import limb_invocation_wrapper
from centipede.limb_timing_manager import TimingManager


class CentipedeBroker(object):
    def __init__(self):
        self.limb_to_next_limb = {}
        self.first_limb = None

        self.limb_name_to_class = {}

        self.limb_processes = []

        self.limb_to_queue = {}
        self.limb_to_queue_lock = {}
        self.limb_is_busy = {}

        self.socket_handler = BrokerCommunicator()
        self.broker_server = threading.Thread(target=self.socket_handler.run_broker_server, args=(self.handle_incoming_data, ))
        self.broker_server.start()

        self.timing_manager = TimingManager()


    def set_limb_pipeline(self, limbs):
        self.first_limb = limbs[0]
        self.timing_manager.init_with_limbs(limbs)
        self.socket_handler.first_limb = limbs[0]
        for i in range(len(limbs)):
            limb_name = limbs[i].__name__

            self.limb_name_to_class[limb_name] = limbs[i]

            if i == len(limbs) - 1:
                self.limb_to_next_limb[limb_name] = None
            else:
                self.limb_to_next_limb[limb_name] = limbs[i+1]

            self.limb_to_queue[limb_name] = deque([])
            self.limb_to_queue_lock[limb_name] = threading.Lock()
            self.limb_is_busy[limb_name] = False


    def create_limb(self, limb, config):
        config_data = pickle.dumps(config)

        new_port = self.socket_handler.get_new_port()

        new_limb_process = multiprocessing.Process(target=limb_invocation_wrapper.create_limb,
                                                   args=(limb, config_data, BROKER_PORT, new_port))
        new_limb_process.start()

        self.limb_processes.append(new_limb_process)
        self.socket_handler.associate_port_with_limb(new_port, limb)


    def handle_incoming_data(self, data):
        data_obj = pickle.loads(data)
        limb_name = data_obj["limb_name"]

        next_limb = self.limb_to_next_limb[limb_name]
        # If there is a next limb, put the data in the queue for the next limb
        if next_limb: # TODO - if there is a queue for the next limb, put it in the queue instead
            self.socket_handler.send_job(next_limb, data)

        # Send another job to that limb if there is one in the queue
        if self.limb_to_queue[limb_name]:
            self.limb_to_queue_lock[limb_name].acquire()
            delivery = self.limb_to_queue[limb_name].popleft()
            self.limb_to_queue_lock[limb_name].release()

            self.timing_manager.record_limb_input(limb_name)
            self.socket_handler.send_job(limb_name, delivery)
            self.limb_is_busy[limb_name] = True
        else:
            self.limb_is_busy[limb_name] = False


    def put_data_in_pipeline(self, data_point):

        first_limb_name = self.first_limb.__name__

        self.timing_manager.record_incoming_job()

        new_package = Package()
        delivery = {}
        delivery["package_data"] = new_package
        delivery["data_point"] = data_point
        delivery["type"] = "job"

        first_limb_is_slow = self.timing_manager.is_limb_slow(None, self.first_limb)
        if first_limb_is_slow or len(self.limb_to_queue[first_limb_name]) > 3:
            print("First limb is slow; we should spawn a new one.")

        limb_is_busy = self.limb_is_busy[first_limb_name]
        if limb_is_busy:
            self.limb_to_queue_lock[first_limb_name].acquire()
            self.limb_to_queue[first_limb_name].append(delivery)
            self.limb_to_queue_lock[first_limb_name].release()
        else:
            self.timing_manager.record_limb_input(first_limb_name)
            self.socket_handler.send_job(first_limb_name, delivery)
            self.limb_is_busy[first_limb_name] = True
