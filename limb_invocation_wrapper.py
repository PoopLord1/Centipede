import json
import socket
import dill as pickle
import threading

BROKER_IP = "127.0.0.1"
LIMB_IP = "127.0.0.1"
LIMB_DATA_PORT = 12344


class LimbInvoker(object):
    def __init__(self, limb_class, config, broker_port):
        self.incoming_data_point = None
        self.incoming_package = None
        self.outgoing_data_client = None

        self.ingest_data_lock = threading.Lock()

        self.limb_thread = threading.Thread(target=self.run_ingestion_process, args=(limb_class, config, broker_port, ))
        self.limb_thread.start()

    def run_ingestion_process(self, limb_class, in_config, broker_port):
        limb_obj = limb_class(in_config)

        # self.outgoing_data_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.outgoing_data_client.connect((BROKER_IP, broker_port))

        while True:

            data_point = None
            package = None

            self.ingest_data_lock.acquire()
            if self.incoming_data_point and self.incoming_package:
                data_point = self.incoming_data_point
                package = self.incoming_package
                self.incoming_package = None
                self.incoming_data_point = None
            self.ingest_data_lock.release()

            if data_point and package:
                limb_obj.scrape_from_url(data_point, package)

                pickled_package = pickle.dumps(package)
                # self.outgoing_data_client.sendall(pickled_package)

    def run_ingestion_server(self, limb_port):
        incoming_data_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        incoming_data_server.bind((LIMB_IP, limb_port))
        incoming_data_server.listen()
        conn, addr = incoming_data_server.accept()

        while True:
            try:
                data = conn.recv(2048)
            except ConnectionResetError as e:
                conn.close()
                incoming_data_server.close()
                incoming_data_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                incoming_data_server.bind((LIMB_IP, limb_port))
                incoming_data_server.listen()
                conn, addr = incoming_data_server.accept()
                continue


            if data:
                inc_object = pickle.loads(data)

                if inc_object["type"] == "job":
                    if not self.incoming_data_point and not self.incoming_package:

                        new_package = inc_object["package_data"]
                        self.ingest_data_lock.acquire()
                        self.incoming_package = new_package
                        self.incoming_data_point = inc_object["data_point"]
                        self.ingest_data_lock.release()
                        # conn.sendall(b"enqueued")

                elif inc_object["type"] == "is_working":
                    pass
                    # if not self.incoming_data_point and not self.incoming_package:
                    #     conn.sendall(b"available")
                    # else:
                    #     conn.sendall(b"working")

                conn.close()
                incoming_data_server.close()
                incoming_data_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                incoming_data_server.bind((LIMB_IP, limb_port))
                incoming_data_server.listen()
                conn, addr = incoming_data_server.accept()

            # Some more clauses here, like timing stuff? idk


def create_limb(limb_class, in_config, broker_port, limb_port):
    invoker = LimbInvoker(limb_class, in_config, broker_port)
    invoker.run_ingestion_server(limb_port)
