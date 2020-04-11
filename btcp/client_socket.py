from btcp.btcp_socket import BTCPSocket
from btcp.constants import *
from btcp.lossy_layer import LossyLayer
import socket
import random
import struct


# bTCP client socket
# A client application makes use of the services provided by bTCP by calling connect, send, disconnect, and close


class BTCPClientSocket(BTCPSocket):
    def __init__(self, window, timeout):
        super().__init__(window, timeout)
        self._lossy_layer = LossyLayer(self, CLIENT_IP, CLIENT_PORT, SERVER_IP, SERVER_PORT)
        self._tcp_sock = socket.socket(socket.AF_INET,
                                       socket.SOCK_DGRAM)  # We use the underscore to hint that the variable is used for internal use
        self._tcp_sock.bind((CLIENT_IP, CLIENT_PORT))
        self._tcp_sock.settimeout(timeout)

    # Called by the lossy layer from another thread whenever a segment arrives. 
    def lossy_layer_input(self, segment):
        pass

    # Perform a three-way handshake to establish a connection
    def connect(self):
        syn_number = random.getrandbits(16)
        print(syn_number)
        print("{0:016b}".format(syn_number))
        ack_number = 0
        data_length = 0
        syn = 0
        ack = 0
        fin = 0
        flags = self.flags_to_int(syn, ack, fin)
        print(flags)
        self._window = 100
        checksum = 0
        packet = struct.pack('HHBBHH', syn_number, ack_number, flags, self._window, data_length, checksum)
        print(packet)
        print(struct.unpack('HHBBHH', packet))
        BTCPSocket.in_cksum(packet)

        pass

    def flags_to_int(self, syn, ack, fin):
        flagBitstring = "{0:0b}".format(syn)
        flagBitstring += "{0:0b}".format(ack)
        flagBitstring += "{0:0b}".format(fin)

        return int(flagBitstring, 2)

    # Send data originating from the application in a reliable way to the server
    def send(self, data):
        pass

    # Perform a handshake to terminate a connection
    def disconnect(self):
        pass

    # Clean up any state
    def close(self):
        self._lossy_layer.destroy()
