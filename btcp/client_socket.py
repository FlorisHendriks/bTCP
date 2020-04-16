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
        self._Disconnected = False
        self._ReceivedPacket = None
        self._timeout = timeout
        self._First_Packet_Sequence_Number = 0
        self._ReceivedAckPackets = []

    # Called by the lossy layer from another thread whenever a segment arrives. 
    def lossy_layer_input(self, segment):
        packet_bytes, address = segment
        self._ReceivedAckPackets.append(packet_bytes)
        self._ReceivedPacket = packet_bytes

    # Perform a three-way handshake to establish a connection
    def connect(self):
        while not self._HandshakeSuccessful:
            self._ReceivedPacket = None
            try:
                header = Header(random.getrandbits(15) & 0xffff, 0, Flags(1,0,0), self._window, 0, 0) #We use 15 bits instead of 16 because there are cases that random.getrandbits() returns a large integer that will overflow the 16 bit length when we add sequence numbers to it and eventually results in an error (struct.error: ushort format requires 0 <= number <= 0xffff)
                Syn_packet = Packet(header, "syn")
                Syn_packet_bytes = Syn_packet.pack_packet()
                print(str(Syn_packet))
                self._lossy_layer.send_segment(Syn_packet_bytes)
                self.wait_for_packet()
                Syn_Ack_Packet_bytes = self._ReceivedPacket
                Syn_Ack_Packet = Packet.unpack_packet(Syn_Ack_Packet_bytes)
                print(Syn_Ack_Packet)
                self._First_Packet_Sequence_Number = Syn_Ack_Packet.getHeader().getAckNumber() + 1
                Ack_number = Syn_Ack_Packet.getHeader().getSynNumber() + 1
                if self._btcpsocket.CheckChecksum(Syn_Ack_Packet_bytes):
                    print("test")
                    Ack_header = Header(0, Ack_number, Flags(0, 1, 0), self._window, 0, 0)
                    Ack_packet = Packet(Ack_header, "ack")
                    Ack_packetBytes = Ack_packet.pack_packet()
                    self._lossy_layer.send_segment(Ack_packetBytes)
                    self._HandshakeSuccessful = True
                    print("handshake succesful")
                else:
                    print("Retry Handshake")
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
        print(type(data))
        packets = []
        content = open(data).read()
        sequence_number_updated = self._First_Packet_Sequence_Number
        while len(content) > 0:
            if len(content) >= 1008:
                header = Header(sequence_number_updated, 0, Flags(0,0,0), self._window, 1008, 0)
                packet = Packet(header, content[:1008])
                packet_bytes = packet.pack_packet()
                content = content[1008:]
                sequence_number_updated += 1008
                packets.append(packet_bytes)
            else:
                header = Header(sequence_number_updated, 0, Flags(0,0,0), self._window, len(content), 0)
                packet = Packet(header, content)
                packet_bytes = packet.pack_packet()
                packets.append(packet_bytes)
                sequence_number_updated += len(content)
                content = ""

        for i in range (0, len(packets)):
            self._lossy_layer.send_segment(packets[i])

        while not Packet.unpack_packet(self._ReceivedPacket).getHeader().getAckNumber() == sequence_number_updated:
            time.sleep(0.1)

        pass

    # Perform a handshake to terminate a connection
    def disconnect(self):
        self._ReceivedPacket = None
        while not self._Disconnected:
            try:
                print("Trying to disconnect:" + "\n")
                header = Header(random.getrandbits(15) & 0xffff, 0, Flags(0,0,1), self._window, 0, 0) #We use 15 bits instead of 16 because there are cases that random.getrandbits() returns a large integer that will overflow the 16 bit length when we add sequence numbers to it and eventually results in an error (struct.error: ushort format requires 0 <= number <= 0xffff)
                Fin_packet = Packet(header, "fin")
                Fin_packet_bytes = Fin_packet.pack_packet()
                print(str(Fin_packet))
                self._lossy_layer.send_segment(Fin_packet_bytes)
                self.wait_for_packet()
                Fin_Ack_Packet_bytes = self._ReceivedPacket
                Fin_Ack_Packet = Packet.unpack_packet(Fin_Ack_Packet_bytes)
                print(Fin_Ack_Packet)
                Ack_number = Fin_Ack_Packet.getHeader().getSynNumber() + 1
                if self._btcpsocket.CheckChecksum(Fin_Ack_Packet_bytes):
                    print("test")
                    Ack_header = Header(0, Ack_number, Flags(0, 1, 0), self._window, 0, 0)
                    Ack_packet = Packet(Ack_header, "ack")
                    Ack_packet_bytes = Ack_packet.pack_packet()
                    self._lossy_layer.send_segment(Ack_packet_bytes)
                    self._Disconnected = True
                    print("disconnection succesful")

                else:
                    print("MonkaS")
            except socket.timeout:
                print("socket timeout")
                pass

    # Clean up any state
    def close(self):
        #self._lossy_layer.destroy()
        pass
