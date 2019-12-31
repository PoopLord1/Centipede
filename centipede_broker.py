import socket
import threading
import json
import pickle

from collections import deque

from centipede.package import Package
from centipede.broker_communicator import BrokerCommunicator

BROKER_PORT = 10000
BROKER_IP = "127.0.0.1"
LIMB_IP = "127.0.0.1"

class CentipedeBroker(object):
    def __init__(self):
        self.limb_to_next_limb = {}
        self.first_limb = None

        self.limb_to_queue = {}
        self.limb_to_queue_lock = {}
        self.limb_is_busy = {}

        self.socket_handler = BrokerCommunicator()
        self.broker_server = threading.Thread(target=self.socket_handler.run_broker_server, args=(BROKER_PORT, self.handle_incoming_data))
        self.broker_server.start()

    def associate_port_with_limb(self, port, limb):
        self.socket_handler.limb_to_port[limb.__name__] = port

    def set_limb_pipeline(self, limbs):
        self.first_limb = limbs[0]
        self.socket_handler.first_limb = limbs[0]
        for i in range(len(limbs)):
            limb_name = limbs[i].__name__

            if i == len(limbs) - 1:
                self.limb_to_next_limb[limb_name] = None
            else:
                self.limb_to_next_limb[limb_name] = limbs[i+1]

            self.limb_to_queue[limb_name] = deque([])
            self.limb_to_queue_lock[limb_name] = threading.Lock()
            self.limb_is_busy[limb_name] = False

    def start_broker_server(self, broker_port):
        # also keep a list of the current pipeline
        # and when we get something from a limb, put it in the queue for the next limb

        broker_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        broker_server.bind((BROKER_IP, broker_port))
        broker_server.listen()
        conn, addr = broker_server.accept()

        while True:
            data = conn.recv(2048)

            data_obj = pickle.loads(data)
            limb_name = data_obj["limb_name"]

            next_limb = self.limb_to_next_limb[limb_name]
            if next_limb:
                out_port = self.socket_handler.limb_to_port[next_limb]

                outgoing_data_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                outgoing_data_client.connect((LIMB_IP, out_port))
                outgoing_data_client.sendall(data_obj["package"])
                # _ = self.outgoing_data_client.recv(2048)

            if self.limb_to_queue[limb_name]:
                self.limb_to_queue_lock[limb_name].acquire()
                delivery = self.limb_to_queue[limb_name].popleft()
                self.limb_to_queue_lock[limb_name].release()

                outgoing_data_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                limb_port = self.socket_handler.limb_to_port[limb_name]
                outgoing_data_client.connect((LIMB_IP, limb_port))
                outgoing_data_client.sendall(pickle.dumps(delivery))
                self.limb_is_busy[limb_name] = True
                outgoing_data_client.close()
            else:
                self.limb_is_busy[limb_name] = False

            conn.close()
            broker_server.close()
            broker_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            broker_server.bind((BROKER_IP, broker_port))
            broker_server.listen()
            conn, addr = broker_server.accept()

    def handle_incoming_data(self, data):
        data_obj = pickle.loads(data)
        limb_name = data_obj["limb_name"]

        next_limb = self.limb_to_next_limb[limb_name]
        # If there is a next limb, put the data in the queue for the next limb
        if next_limb:
            out_port = self.socket_handler.limb_to_port[next_limb]

            outgoing_data_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            outgoing_data_client.connect((LIMB_IP, out_port))
            outgoing_data_client.sendall(data_obj["package"])
            # _ = self.outgoing_data_client.recv(2048)

        # Send another job to that limb if there is one in the queue
        if self.limb_to_queue[limb_name]:
            self.limb_to_queue_lock[limb_name].acquire()
            delivery = self.limb_to_queue[limb_name].popleft()
            self.limb_to_queue_lock[limb_name].release()

            outgoing_data_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            limb_port = self.socket_handler.limb_to_port[limb_name]
            outgoing_data_client.connect((LIMB_IP, limb_port))
            outgoing_data_client.sendall(pickle.dumps(delivery))
            self.limb_is_busy[limb_name] = True
            outgoing_data_client.close()
        else:
            self.limb_is_busy[limb_name] = False


    def put_data_in_pipeline(self, data_point):

        first_limb_name = self.first_limb.__name__
        first_port = self.socket_handler.limb_to_port[first_limb_name]

        new_package = Package()
        delivery = {}
        delivery["package_data"] = new_package
        delivery["data_point"] = data_point
        delivery["type"] = "job"

        limb_is_busy = self.limb_is_busy[first_limb_name]
        if limb_is_busy:
            self.limb_to_queue_lock[first_limb_name].acquire()
            self.limb_to_queue[first_limb_name].append(delivery)
            self.limb_to_queue_lock[first_limb_name].release()
        else:
            self.socket_handler.send_job(first_limb_name, delivery)
            self.limb_is_busy[first_limb_name] = True
