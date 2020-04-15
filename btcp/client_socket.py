from btcp.btcp_socket import BTCPSocket
from btcp.constants import *
from btcp.lossy_layer import LossyLayer
from btcp.packet import *
import socket
import random
import time
import struct


# bTCP client socket
# A client application makes use of the services provided by bTCP by calling connect, send, disconnect, and close


class BTCPClientSocket(BTCPSocket):
    def __init__(self, window, timeout):
        super().__init__(window, timeout)
        self._lossy_layer = LossyLayer(self, CLIENT_IP, CLIENT_PORT, SERVER_IP, SERVER_PORT)
        self._btcpsocket = BTCPSocket
        #self._tcp_sock = socket.socket(socket.AF_INET,
                                       #socket.SOCK_DGRAM)  # We use the underscore to hint that the variable is used for internal use
        #self._tcp_sock.bind((CLIENT_IP, CLIENT_PORT))
        #self._tcp_sock.settimeout(timeout)
        #self._server_address = (SERVER_IP, SERVER_PORT)
        self._HandshakeSuccessful = False
        self._ReceivedPacket = None
        self._timeout = timeout

    # Called by the lossy layer from another thread whenever a segment arrives. 
    def lossy_layer_input(self, segment):

        self._ReceivedPacket = segment

    # Perform a three-way handshake to establish a connection
    def connect(self):
        while not self._HandshakeSuccessful:
            try:
                header = Header(random.getrandbits(16), 0, Flags(1,0,0), self._window, 0, 0)
                Syn_packet = Packet(header, "syn")
                Syn_packet_bytes = Syn_packet.pack_packet()
                print(str(Syn_packet))
                self._lossy_layer.send_segment(Syn_packet_bytes)
                self.wait_for_packet()
                Syn_Ack_Packet_bytes, address = self._ReceivedPacket
                Syn_Ack_Packet = Packet.unpack_packet(Syn_Ack_Packet_bytes)
                Syn_number = Syn_Ack_Packet.getHeader().getAckNumber() + 1
                Ack_number = Syn_Ack_Packet.getHeader().getSynNumber() + 1
                if self._btcpsocket.CheckChecksum(Syn_Ack_Packet_bytes):
                    print("test")
                    Ack_header = Header(Syn_number, Ack_number, Flags(0, 1, 0), self._window, 0, 0)
                    Ack_packet = Packet(Ack_header, "ack")
                    Ack_packetBytes = Ack_packet.pack_packet()
                    self._lossy_layer.send_segment(Ack_packetBytes)
                    self._HandshakeSuccessful = True
                    print("handshake succesful")
                else:
                    print("MonkaS")
            except socket.timeout:
                print("socket timeout")
                pass

    def flags_to_int(self, syn, ack, fin):
        flagBitstring = "{0:0b}".format(syn)
        flagBitstring += "{0:0b}".format(ack)
        flagBitstring += "{0:0b}".format(fin)

        return int(flagBitstring, 2)

    def wait_for_packet(self):
        while self._ReceivedPacket is None:
            time.sleep(self._timeout*0.001)
        if self._ReceivedPacket is not None:
            pass
        else:
            self.wait_for_packet()

    # Send data originating from the application in a reliable way to the server
    def send(self, data):
        pass

    # Perform a handshake to terminate a connection
    def disconnect(self):
        pass

    # Clean up any state
    def close(self):
        self._lossy_layer.destroy()
