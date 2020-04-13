import socket
from btcp.lossy_layer import LossyLayer
from btcp.btcp_socket import BTCPSocket
from btcp.constants import *
from btcp.packet import *

# The bTCP server socket
# A server application makes use of the services provided by bTCP by calling accept, recv, and close
class BTCPServerSocket(BTCPSocket):
    def __init__(self, window, timeout):
        super().__init__(window, timeout)
        self._lossy_layer = LossyLayer(self, SERVER_IP, SERVER_PORT, CLIENT_IP, CLIENT_PORT)
        self._tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._tcp_sock.bind((SERVER_IP, SERVER_PORT))
        self._tcp_sock.settimeout(timeout)
        self._client_address = (CLIENT_IP, CLIENT_PORT)

    # Called by the lossy layer from another thread whenever a segment arrives
    def lossy_layer_input(self, segment):
        pass

    # Wait for the client to initiate a three-way handshake
    def accept(self):
        packet_bytes, address = self._tcp_sock.recvfrom(1018)
        packet = Packet.unpack_packet(packet_bytes)

        pass

    # Send any incoming data to the application layer
    def recv(self):
        pass

    # Clean up any state
    def close(self):
        self._lossy_layer.destroy()
