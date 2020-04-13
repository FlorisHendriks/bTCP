from btcp.btcp_socket import BTCPSocket
from btcp.constants import *
from btcp.lossy_layer import LossyLayer
from btcp.packet import *
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
        self._server_address = (SERVER_IP, SERVER_PORT)

    # Called by the lossy layer from another thread whenever a segment arrives. 
    def lossy_layer_input(self, segment):
        pass

    # Perform a three-way handshake to establish a connection
    def connect(self):

        flags = Flags(1,0,0)
        header = Header(random.getrandbits(16), 0, flags, self._window, 0, 0)
        Syn_packet = Packet(header, "test")
        packet_bytes = Syn_packet.pack_packet()
        print(str(Syn_packet))
        self._tcp_sock.sendto(packet_bytes, self._server_address)
        Server_bytes, address = self._tcp_sock.recvfrom(1018)
        if self.CheckChecksum(self, Server_bytes):
            print("dab")
        else:
            print("MonkaS")
        SynAck_packet = Packet.unpack_packet(Server_bytes)





        pass

    def flags_to_int(self, syn, ack, fin):
        flagBitstring = "{0:0b}".format(syn)
        flagBitstring += "{0:0b}".format(ack)
        flagBitstring += "{0:0b}".format(fin)

        return int(flagBitstring, 2)

    def CheckChecksum(self, packet):
        if int(BTCPSocket.in_cksum(packet)) == 0:
            return True
        else:
            return False

    # Send data originating from the application in a reliable way to the server
    def send(self, data):
        pass

    # Perform a handshake to terminate a connection
    def disconnect(self):
        pass

    # Clean up any state
    def close(self):
        self._lossy_layer.destroy()
