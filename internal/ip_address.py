import os
import socket
import fcntl
import struct

ip = ""

if os.name == "nt":
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)

else:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ip = socket.inet_ntoa(fcntl.ioctl(
            sock.fileno(),
            0x8915,
            struct.pack("256s", bytes("eth0", "utf-8")))[20:24])

if __name__ == "__main__":
    print(ip)
