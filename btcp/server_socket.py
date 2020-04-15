import socket
from btcp.lossy_layer import LossyLayer
from btcp.btcp_socket import BTCPSocket
from btcp.constants import *
from btcp.packet import *
import random

# The bTCP server socket
# A server application makes use of the services provided by bTCP by calling accept, recv, and close
class BTCPServerSocket(BTCPSocket):
    def __init__(self, window, timeout):
        super().__init__(window, timeout)
        self._lossy_layer = LossyLayer(self, SERVER_IP, SERVER_PORT, CLIENT_IP, CLIENT_PORT)
        #self._tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #self._tcp_sock.bind((SERVER_IP, SERVER_PORT))
        #self._tcp_sock.settimeout(timeout)
        #self._client_address = (CLIENT_IP, CLIENT_PORT)
        self._HandshakeSuccessful = False
        self._ReceivedPacket = None

    # Called by the lossy layer from another thread whenever a segment arrives
    def lossy_layer_input(self, segment):
        self._ReceivedPacket = segment
        pass

    # Wait for the client to initiate a three-way handshake
    def accept(self):
        while self._ReceivedPacket is None:
            pass
        Syn_Ack_packet_bytes = self._ReceivedPacket
        flags = Flags(1,1,0)
        print(Syn_Ack_packet_bytes)
        packet = Packet.unpack_packet(Syn_Ack_packet_bytes)
        print(packet.getHeader().getSynNumber())
        ack_number = packet.getHeader().getSynNumber() + 1
        header = Header(random.getrandbits(16), ack_number, flags, self._window, 0, 0)
        Syn_Ack_packet = Packet(header, "syn_ack")
        self._lossy_layer.send_segment(Syn_Ack_packet.pack_packet())
        AckPacket_bytes = self._ReceivedPacket
        print(AckPacket_bytes)
        print(Packet.unpack_packet(AckPacket_bytes))
        self._lossy_layer.destroy()
        pass

    # Send any incoming data to the application layer
    def recv(self):
        pass

    # Clean up any state
    def close(self):
        self._lossy_layer.destroy()
