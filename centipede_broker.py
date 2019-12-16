import socket
import json
import pickle

from centipede.package import Package

LIMB_IP = "127.0.0.1"
BROKER_IP = "127.0.0.1"


class CentipedeBroker(object):
    def __init__(self):
        self.ports_to_limbs = {}
        self.limb_to_port = {}
        self.limb_to_next_limb = {}
        self.first_limb = None

    def associate_port_with_limb(self, port, limb):
        self.ports_to_limbs[port] = limb
        self.limb_to_port[limb] = port

    def set_limb_pipeline(self, limbs):
        self.first_limb = limbs[0]
        for i in range(len(limbs)):
            if i == len(limbs) - 1:
                self.limb_to_next_limb[limbs[i]] = None
            else:
                self.limb_to_next_limb[limbs[i]] = limbs[i+1]

    def start_broker_server(self, broker_port):
        # also keep a list of the current pipeline
        # and when we get something from a limb, put it in the queue for the next limb

        broker_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        broker_server.bind((BROKER_IP, broker_port))
        broker_server.listen()
        conn, addr = broker_server.accept()

        while True:
            data = conn.recv(2048)

            data_obj = json.loads(data)
            limb_name = data_obj["limb_name"]

            next_limb = self.limb_to_next_limb[limb_name]
            if next_limb:
                out_port = self.limb_to_port[next_limb]

                outgoing_data_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                outgoing_data_client.connect((LIMB_IP, out_port))
                outgoing_data_client.sendall(data_obj["package"])
                # _ = self.outgoing_data_client.recv(2048)

    def put_data_in_pipeline(self, data_point):

        first_port = self.limb_to_port[self.first_limb]

        outgoing_data_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        outgoing_data_client.connect((LIMB_IP, first_port))

        new_package = Package()
        delivery = {}
        delivery["package_data"] = new_package
        delivery["data_point"] = data_point
        delivery["type"] = "job"
        outgoing_data_client.sendall(pickle.dumps(delivery))
        outgoing_data_client.close()
