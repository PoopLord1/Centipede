import threading
import pickle
import multiprocessing
import uuid

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

        self.limb_to_process_ids = {}
        self.limb_to_queue = {}
        self.limb_to_queue_lock = {}
        self.limb_to_config = {}

        self.process_id_is_busy = {}
        self.id_to_process = {}

        self.socket_handler = BrokerCommunicator()
        self.broker_server = threading.Thread(target=self.socket_handler.run_broker_server, args=(self.handle_incoming_data, ))
        self.broker_server.start()

        self.timing_manager = TimingManager()


    def save_limb_config(self, limb, config):
        self.limb_to_config[limb.__name__] = config


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

            self.limb_to_process_ids[limb_name] = []


    def create_process(self, limb):
        limb_name = limb.__name__
        config = self.limb_to_config[limb_name]
        config_data = pickle.dumps(config)

        new_port = self.socket_handler.get_new_port()

        new_process = multiprocessing.Process(target=limb_invocation_wrapper.create_limb,
                                                   args=(limb, config_data, BROKER_PORT, new_port))
        new_process.start()

        process_id = uuid.uuid4()
        self.limb_to_process_ids[limb_name].append(process_id)
        self.id_to_process[process_id] = new_process
        self.process_id_is_busy[process_id] = False

        self.socket_handler.associate_port_with_process_id(new_port, process_id)


    def handle_incoming_data(self, data):
        data_obj = pickle.loads(data)
        limb_name = data_obj["limb_name"]

        next_limb = self.limb_to_next_limb[limb_name]
        # If there is a next limb, put the data in the queue for the next limb
        if next_limb:

            next_limb_is_slow = self.timing_manager.is_limb_slow(limb_name, next_limb)
            next_limb_name = next_limb.__name__
            if next_limb_is_slow or len(self.limb_to_queue[next_limb_name]) > 3:
                self.create_process(next_limb)
                self.timing_manager.reset_timing_info(next_limb)

            free_process = None
            for process in self.limb_to_process_ids[next_limb_name]:
                if not self.process_id_is_busy[process]:
                    free_process = process
                    break

            if free_process:
                self.timing_manager.record_limb_input(next_limb_name)

                new_data = data_obj.copy()
                new_data["limb_name"] = next_limb_name
                new_data["process_id"] = free_process
                new_data["type"] = "job"

                self.socket_handler.send_job(free_process, new_data)
            else:
                self.limb_to_queue_lock[next_limb_name].acquire()
                self.limb_to_queue[next_limb_name].append(data)
                self.limb_to_queue_lock[next_limb_name].release()

        # Send another job to that limb if there is one in the queue
        if self.limb_to_queue[limb_name]:
            self.limb_to_queue_lock[limb_name].acquire()
            delivery = self.limb_to_queue[limb_name].popleft()
            self.limb_to_queue_lock[limb_name].release()

            delivery["limb_name"] = data_obj["limb_name"]
            delivery["process_id"] = data_obj["process_id"]
            delivery["type"] = "job"

            self.timing_manager.record_limb_input(limb_name)
            self.socket_handler.send_job(data_obj["process_id"], delivery)
            self.process_id_is_busy[data_obj["process_id"]] = True
        else:
            self.process_id_is_busy[data_obj["process_id"]] = False


    def put_data_in_pipeline(self, data_point):

        first_limb_name = self.first_limb.__name__

        self.timing_manager.record_incoming_job()

        new_package = Package()
        delivery = {}
        delivery["package_data"] = new_package
        delivery["data_point"] = data_point
        delivery["limb_name"] = first_limb_name
        delivery["type"] = "job"

        first_limb_is_slow = self.timing_manager.is_limb_slow(None, self.first_limb)
        if first_limb_is_slow or len(self.limb_to_queue[first_limb_name]) > 3:
            self.create_process(self.first_limb)
            self.timing_manager.reset_timing_info(self.first_limb)

        free_process = None
        for process_id in self.limb_to_process_ids[first_limb_name]:
            if not self.process_id_is_busy[process_id]:
                free_process = process_id
                break

        if free_process:
            delivery["process_id"] = free_process
            self.timing_manager.record_limb_input(first_limb_name)
            self.socket_handler.send_job(free_process, delivery)
            self.process_id_is_busy[free_process] = True
        else:
            self.limb_to_queue_lock[first_limb_name].acquire()
            self.limb_to_queue[first_limb_name].append(delivery)
            self.limb_to_queue_lock[first_limb_name].release()
