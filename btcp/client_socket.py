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
        self._HandshakeSuccessful = False
        self._Disconnected = False
        self._timeout = timeout
        self._First_Packet_Sequence_Number = 0
        self._PacketList = []
        self._AckPacket = None
        self._SequenceNumberList = []
        self._Packetloss = 0
        self._packets1 = []
        self._retryCounter = 10


    # Called by the lossy layer from another thread whenever a segment arrives. 
    def lossy_layer_input(self, segment):
        packet_bytes, address = segment
        self._PacketList.append(packet_bytes)

    # Perform a three-way handshake to establish a connection
    def connect(self):
        print("Trying handshake (client-sided)")
        while self._retryCounter >= 0 and not self._HandshakeSuccessful:
            self._PacketList = []
            header = Header(random.getrandbits(15) & 0xffff, 0, Flags(1,0,0), self._window, 0, 0) #We use 15 bits instead of 16 because there are cases that random.getrandbits() returns a large integer that will overflow the 16 bit length when we add sequence numbers to it and eventually results in an error (struct.error: ushort format requires 0 <= number <= 0xffff)
            Syn_packet = Packet(header, "")
            Syn_packet_bytes = Syn_packet.pack_packet()
            self._lossy_layer.send_segment(Syn_packet_bytes)
            if self.wait_for_packet():
                Syn_Ack_Packet_bytes = self._PacketList[0]
                Syn_Ack_Packet = Packet.unpack_packet(Syn_Ack_Packet_bytes)
                self._First_Packet_Sequence_Number = Syn_Ack_Packet.getHeader().getAckNumber()
                Ack_number = Syn_Ack_Packet.getHeader().getSynNumber() + 1
                if self._btcpsocket.CheckChecksum(Syn_Ack_Packet_bytes):
                    Ack_header = Header(0, Ack_number, Flags(0, 1, 0), self._window, 0, 0)
                    Ack_packet = Packet(Ack_header, "")
                    self._AckPacket = Ack_packet
                    Ack_packetBytes = Ack_packet.pack_packet()
                    self._lossy_layer.send_segment(Ack_packetBytes)
                    self._HandshakeSuccessful = True
                    print("Client handshake successful")
                    self._PacketList = []
                else:
                    print("Retrying handshake, the checksum of the syn-ack packet is invalid")
                    self._retryCounter -= 1

            else:
                print("Retrying handshake, packet timeout")
                self._retryCounter -= 1
        if self._retryCounter < 0:
            print("Number of tries exceed, quitting connection...")

    def wait_for_packet(self):
        timeNow = time.time()
        while self._PacketList == [] and time.time() < timeNow + self._timeout * 0.001:
            time.sleep(0.001)
        if not self._PacketList:
            return False
        else:
            return True

    # Send data originating from the application in a reliable way to the server
    def send(self, data):
        packets = []
        content = open(data).read()
        sequence_number_updated = self._First_Packet_Sequence_Number

        # Making packet bytes from the input file
        while len(content) > 0:
            if len(content) >= 1008:
                header = Header(sequence_number_updated, 0, Flags(0,0,0), self._window, 1008, 0)
                packet = Packet(header, content[:1008])
                packet_bytes = packet.pack_packet()
                content = content[1008:]
                self._SequenceNumberList.append(sequence_number_updated)
                sequence_number_updated += 1008
                packets.append(packet_bytes)
            else:
                header = Header(sequence_number_updated, 0, Flags(0,0,0), self._window, len(content), 0)
                packet = Packet(header, content)
                packet_bytes = packet.pack_packet()
                packets.append(packet_bytes)
                self._SequenceNumberList.append(sequence_number_updated)
                sequence_number_updated += len(content)
                content = ""

        # Sending the packets to the client
        packet_length = len(packets)
        i = 0
        k = self._window
        while packet_length > self._window:
            packet_length = packet_length - self._window
            for j in range(i, k):
                self.ResubmitPacket(packets[j])
            i += self._window
            k += self._window
        for m in range(i, len(packets)):
            self.ResubmitPacket(packets[m])

    # We implemented a stop-and-wait protocol, every packet we send to the server we wait until we receive the right ack
    # packet from the server, else we resend the packet
    def ResubmitPacket(self, packetbytes):
        self._PacketList = []
        self._lossy_layer.send_segment(packetbytes)
        while not self.wait_for_packet():
            self._lossy_layer.send_segment(packetbytes)
        packet = Packet.unpack_packet(packetbytes)
        while not self.CheckIfAckPacketAndCorrectNumber(packet.getHeader().getSynNumber() + packet.getHeader().getDatalength()):
            if Packet.unpack_packet(self._PacketList[0]).getHeader().getFlags().flag_to_int() == 6:
                self._lossy_layer.send_segment(self._AckPacket.pack_packet())
                self._PacketList = []
                while not self.wait_for_packet():
                    self._lossy_layer.send_segment(self._AckPacket.pack_packet())
            else:
                self._lossy_layer.send_segment(packetbytes)
                self._PacketList = []
                while not self.wait_for_packet():
                    self._lossy_layer.send_segment(packetbytes)

    # Check if the ack packet we receive from the server coincides with the data packet we just sent
    def CheckIfAckPacketAndCorrectNumber(self, SynNumber):
        if Packet.unpack_packet(self._PacketList[0]).getHeader().getFlags().flag_to_int() == 2 and Packet.unpack_packet(self._PacketList[0]).getHeader().getAckNumber() == SynNumber:
            return True

        for i in range(0, len(self._SequenceNumberList)):
            if Packet.unpack_packet(self._PacketList[0]).getHeader().getAckNumber() == self._SequenceNumberList[i]:
                self._Packetloss = i
        return False

    # Perform a handshake to terminate a connection
    def disconnect(self):
        print("Trying to disconnect (client-sided):")
        self._retryCounter = 10
        while self._retryCounter >= 0 and not self._Disconnected:
            self._PacketList = []
            header = Header(random.getrandbits(15) & 0xffff, 0, Flags(0,0,1), self._window, 0, 0) #We use 15 bits instead of 16 because there are cases that random.getrandbits() returns a large integer that will overflow the 16 bit length when we add sequence numbers to it and eventually results in an error (struct.error: ushort format requires 0 <= number <= 0xffff)
            Fin_packet = Packet(header, "fin")
            Fin_packet_bytes = Fin_packet.pack_packet()
            self._lossy_layer.send_segment(Fin_packet_bytes)
            if self.wait_for_packet():
                if Packet.unpack_packet(self._PacketList[0]).getHeader().getFlags().flag_to_int() == 3:
                    Fin_Ack_Packet_bytes = self._PacketList[0]
                    self._PacketList.pop(0)
                    Fin_Ack_Packet = Packet.unpack_packet(Fin_Ack_Packet_bytes)
                    Ack_number = Fin_Ack_Packet.getHeader().getSynNumber() + 1
                    if self._btcpsocket.CheckChecksum(Fin_Ack_Packet_bytes):
                        Ack_header = Header(0, Ack_number, Flags(0, 1, 0), self._window, 0, 0)
                        Ack_packet = Packet(Ack_header, "ack")
                        Ack_packet_bytes = Ack_packet.pack_packet()
                        self._lossy_layer.send_segment(Ack_packet_bytes)
                        self._Disconnected = True
                        print("Client disconnection successful")
                    else:
                        print("Retrying disconnection, the checksum of the fin-ack packet is invalid")
                        self._retryCounter -= 1
                else:
                    print("Retrying handshake, the received packet is not a fin-ack packet")
                    self._retryCounter -= 1
            else:
                print("Retrying handshake, packet timeout")
                self._retryCounter -= 1
        if self._retryCounter < 0:
            print("Number of tries exceeded, going to disconnect")
            self._Disconnected = True

    # Clean up any state and close the socket
    def close(self):
        self._lossy_layer.destroy()
        pass
