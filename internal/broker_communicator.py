import socket
import dill 

from centipede.internal.ip_address import ip as BROKER_IP

BROKER_PORT = 10000
LIMB_PORT_RANGE_START = 10001


class BrokerCommunicator(object):
    def __init__(self):
        self.first_limb = None
        self.process_id_to_port = {}
        self.process_id_to_ip = {}

        self.next_unused_port = LIMB_PORT_RANGE_START


    def send_job(self, process_id, delivery):
        port = self.process_id_to_port[process_id]
        ip = self.process_id_to_ip[process_id]

        outgoing_data_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        outgoing_data_client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        outgoing_data_client.connect((ip, port))
        outgoing_data_client.sendall(dill.dumps(delivery))
        outgoing_data_client.close()


    def associate_port_with_process_id(self, port, process_id):
        self.process_id_to_port[process_id] = port


    def associate_ip_with_process_id(self, ip, process_id):
        self.process_id_to_ip[process_id] = ip


    def run_broker_server(self, incoming_data_handler):
        # also keep a list of the current pipeline
        # and when we get something from a limb, put it in the queue for the next limb

        broker_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        broker_server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        broker_server.bind(("", BROKER_PORT))
        broker_server.listen()
        conn, addr = broker_server.accept()

        while True:
            data = conn.recv(16384) # TODO - put in a layer similar to TCP where we join our packets together?

            return_string = incoming_data_handler(data)

            if return_string:
                conn.send(return_string)

            conn.close()
            conn, addr = broker_server.accept()


    def get_new_port(self):
        new_port = self.next_unused_port
        self.next_unused_port += 1
        return new_port

