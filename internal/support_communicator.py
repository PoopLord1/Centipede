import dill
import socket

SUPPORTER_PORT = 12000

class SupportCommunicator(object):

    next_open_port = SUPPORTER_PORT + 1

    def __init__(self):
        hostname = socket.gethostname()
        self.supporter_ip = socket.gethostbyname(hostname)
        self.supporter_port = SUPPORTER_PORT

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


    def register_supporter(self, broker_ip, broker_port):
        new_process_info = {}
        new_process_info["type"] = "new_support"
        new_process_info["port"] = self.supporter_port
        new_process_info["ip"] = self.supporter_ip

        outgoing_data_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        outgoing_data_client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        outgoing_data_client.connect((broker_ip, broker_port))
        outgoing_data_client.sendall(dill.dumps(new_process_info))

        resp = outgoing_data_client.recv(2048)
        outgoing_data_client.close()
        return resp


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