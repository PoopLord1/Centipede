
import socket
import pickle

LIMB_IP = "127.0.0.1"
BROKER_IP = "127.0.0.1"

class BrokerCommunicator(object):
	def __init__(self):
		self.first_limb = None
		self.limb_to_port = {}

	def send_job(self, limb_name, delivery):
		# TODO - expand this to work with limbs other than the first one
		first_port = self.limb_to_port[self.first_limb.__name__]
		outgoing_data_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		outgoing_data_client.connect((LIMB_IP, first_port))
		outgoing_data_client.sendall(pickle.dumps(delivery))
		outgoing_data_client.close()


	def run_broker_server(self, broker_port, incoming_data_handler):
		# also keep a list of the current pipeline
		# and when we get something from a limb, put it in the queue for the next limb

		broker_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		broker_server.bind((BROKER_IP, broker_port))
		broker_server.listen()
		conn, addr = broker_server.accept()

		while True:
			data = conn.recv(2048)

			incoming_data_handler(data)

			conn.close()
			broker_server.close()
			broker_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			broker_server.bind((BROKER_IP, broker_port))
			broker_server.listen()
			conn, addr = broker_server.accept()
