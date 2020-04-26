import socket
import dill
import threading
import multiprocessing
import uuid

from centipede.internal import limb_invocation_wrapper
from centipede.internal.support_communicator import SupportCommunicator

BROKER_PORT = 10000

class Supporter(object):

    def __init__(self, master_ip):
        self.master_ip = master_ip

        self.communicator = SupportCommunicator()

        self.server_thread = threading.Thread(target=self.communicator.start_network_thread, args=(self.handle_incoming_data,))

        self.process_id_to_processes = {}

        resp = self.communicator.register_supporter(master_ip, BROKER_PORT)
        self.handle_incoming_data(resp)


    def start_support(self):
        self.server_thread.start()


    def handle_incoming_data(self, inc_data):
        data_obj = dill.loads(inc_data)

        if data_obj["type"] == "class_list":
            self.handle_class_list(data_obj)

        elif data_obj["type"] == "new_process":
            pass # spawn a new process for the included class
            # TODO


    def handle_class_list(self, data_obj):
        class_list = data_obj["classes"]
        broker_ip = data_obj["broker_ip"]
        broker_port = data_obj["broker_port"]
        for _class in class_list:
            class_name = _class.__name__
            config_data = data_obj["configs"][class_name]

            new_limb_port = self.communicator.next_open_port
            self.communicator.next_open_port += 1

            new_process = multiprocessing.Process(target=limb_invocation_wrapper.create_limb,
                                                  args=(_class, config_data, broker_ip, broker_port, new_limb_port))

            process_id = str(uuid.uuid4())
            self.process_id_to_processes[process_id] = new_process

            self.communicator.register_support_process(broker_ip, broker_port, class_name, process_id, new_limb_port)


