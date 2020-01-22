import socket
import pickle

BROKER_PORT = 10000
LIMB_PORT_RANGE_START = 10001

LIMB_IP = "127.0.0.1"
BROKER_IP = "127.0.0.1"


class BrokerCommunicator(object):
    def __init__(self):
        self.first_limb = None
        self.limb_to_port = {}

        self.next_unused_port = LIMB_PORT_RANGE_START


    def send_job(self, limb_name, delivery):
        # TODO - expand this to work with limbs other than the first one
        port = self.limb_to_port[limb_name]
        outgoing_data_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        outgoing_data_client.connect((LIMB_IP, port))
        outgoing_data_client.sendall(pickle.dumps(delivery))
        outgoing_data_client.close()


    def associate_port_with_limb(self, port, limb):
        self.limb_to_port[limb.__name__] = port


    def run_broker_server(self, incoming_data_handler):
        # also keep a list of the current pipeline
        # and when we get something from a limb, put it in the queue for the next limb

        broker_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        broker_server.bind((BROKER_IP, BROKER_PORT))
        broker_server.listen()
        conn, addr = broker_server.accept()

        while True:
            data = conn.recv(2048)

            incoming_data_handler(data)

            conn.close()
            broker_server.close()
            broker_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            broker_server.bind((BROKER_IP, BROKER_PORT))
            broker_server.listen()
            conn, addr = broker_server.accept()


    def get_new_port(self):
        new_port = self.next_unused_port
        self.next_unused_port += 1
        return new_port

