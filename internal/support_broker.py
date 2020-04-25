import socket
import dill
import threading
import multiprocessing
import uuid

from centipede.internal import limb_invocation_wrapper

SUPPORTER_PORT = 12000
BROKER_PORT = 10000

class SupportBroker(object):

    next_open_port = SUPPORTER_PORT + 1

    def __init__(self, master_ip):
        self.master_ip = master_ip

        hostname = socket.gethostname()
        self.supporter_ip = socket.gethostbyname(hostname)
        self.supporter_port = SUPPORTER_PORT

        self.server_thread = threading.Thread(target=self.start_network_thread, args=(self.handle_incoming_data,))

        self.process_id_to_processes = {}

        self.register_supporter(master_ip, BROKER_PORT)


    def start_support(self):
        self.server_thread.start()


    def register_supporter(self, broker_ip, broker_port):
        new_process_info = {}
        new_process_info["type"] = "new_support"
        new_process_info["port"] = self.supporter_port
        new_process_info["ip"] = self.supporter_ip

        outgoing_data_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        outgoing_data_client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        outgoing_data_client.connect((broker_ip, broker_port))
        outgoing_data_client.sendall(dill.dumps(new_process_info))

        resp = outgoing_data_client.recv(1024)
        outgoing_data_client.close()
        self.handle_incoming_data(resp)


    def register_support_process(self, broker_ip, broker_port, class_name, process_id, process_port):
        # send data to the broker to enlist the new process
        new_process_info = {}
        new_process_info["type"] = "new_process"
        new_process_info["port"] = process_port
        new_process_info["ip"] = self.supporter_ip
        new_process_info["class"] = class_name
        new_process_info["process_id"] = process_id


        outgoing_data_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        outgoing_data_client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        outgoing_data_client.connect((broker_ip, broker_port))
        outgoing_data_client.sendall(dill.dumps(new_process_info))
        outgoing_data_client.close()


    def request_class_information(self):
        # make a request to the broker for the class information needed
        pass


    def start_network_thread(self, incoming_data_handler):
        broker_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        broker_server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        broker_server.bind((self.supporter_ip, self.supporter_port))
        broker_server.listen()
        conn, addr = broker_server.accept()

        while True:
            data = conn.recv(2048)

            return_string = incoming_data_handler(data)

            if return_string:
                conn.send(return_string)

            conn.close()
            conn, addr = broker_server.accept()


    def handle_incoming_data(self, inc_data):
        data_obj = dill.loads(inc_data)

        if data_obj["type"] == "class_list":
            class_list = data_obj["classes"]
            broker_ip = data_obj["broker_ip"]
            broker_port = data_obj["broker_port"]
            for _class in class_list:
                class_name = _class.__name__
                config_data = data_obj["configs"][class_name]

                new_limb_port = SupportBroker.next_open_port
                SupportBroker.next_open_port += 1

                new_process = multiprocessing.Process(target=limb_invocation_wrapper.create_limb,
                                                      args=(_class, config_data, broker_ip, broker_port, new_limb_port))

                process_id = str(uuid.uuid4())
                self.process_id_to_processes[process_id] = new_process

                self.register_support_process(broker_ip, broker_port, class_name, process_id, new_limb_port)

        elif data_obj["type"] == "new_process":
            pass # spawn a new process for the included class
            # TODO



