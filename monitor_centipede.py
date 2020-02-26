from asciimatics.screen import Screen
from asciimatics.scene import Scene
from asciimatics.effects import Cycle, Stars
from asciimatics.renderers import FigletText

import time
import socket
import pickle

PORT = 10000
BROKER_IP = "127.0.0.1"

class CentipedeMonitor():
    def __init__(self):
        pass

    def fetch_data(self):
        # TODO make a request to centipede for the information
        delivery = {}
        delivery["type"] = "status"

        outgoing_data_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        outgoing_data_client.connect((BROKER_IP, PORT))
        outgoing_data_client.sendall(pickle.dumps(delivery))
        data = outgoing_data_client.recv(4096)
        outgoing_data_client.close()

        return data

    def visualize_data(self, data, screen):

        screen.clear()
        line_counter = 0
        for limb_dict in data:

            screen.print_at(limb_dict["title"] + "  -  " + str(limb_dict["Processing Rate"]), 0, line_counter)
            line_counter += 1

            if "Queue Size" in limb_dict.keys():
                screen.print_at(str(limb_dict["Queue Size"]) + " jobs in queue.", 2, line_counter)
                line_counter += 1

            if "Processes" in limb_dict.keys():
                for process in limb_dict["Processes"]:

                    if process["Status"]:
                        screen.print_at("•", 2, line_counter, Screen.COLOUR_GREEN)
                    else:
                        screen.print_at("•", 2, line_counter, Screen.COLOUR_RED)
                    screen.print_at(process["Process ID"] + "  -  " + str(process["Processing Rate"]), 4, line_counter)
                    line_counter += 1

            line_counter += 1
        screen.refresh()


    def work(self, screen):
        while True:
            data = self.fetch_data()
            self.visualize_data(pickle.loads(data), screen)

            time.sleep(2)


def main():
    monitor_obj = CentipedeMonitor()
    Screen.wrapper(monitor_obj.work)

main()