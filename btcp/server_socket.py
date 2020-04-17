import socket
from btcp.lossy_layer import LossyLayer
from btcp.btcp_socket import BTCPSocket
from btcp.constants import *
from btcp.packet import *
import random
import time
# The bTCP server socket
# A server application makes use of the services provided by bTCP by calling accept, recv, and close
class BTCPServerSocket(BTCPSocket):
    def __init__(self, window, timeout):
        self._btcpsocket = BTCPSocket
        super().__init__(window, timeout)
        self._lossy_layer = LossyLayer(self, SERVER_IP, SERVER_PORT, CLIENT_IP, CLIENT_PORT)
        #self._tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #self._tcp_sock.bind((SERVER_IP, SERVER_PORT))
        #self._tcp_sock.settimeout(timeout)
        #self._client_address = (CLIENT_IP, CLIENT_PORT)
        self._HandshakeSuccessful = False
        self._Disconnected = False
        self._ReceivedPacket = None
        self._PacketList = []


    # Called by the lossy layer from another thread whenever a segment arrives
    def lossy_layer_input(self, segment):
        #print(segment)
        packet_bytes, address = segment
        self._PacketList.append(packet_bytes)
        self._ReceivedPacket = packet_bytes
        pass

    # Wait for the client to initiate a three-way handshake
    def accept(self):
        self._ReceivedPacket = None
        print("test")
        while not self._HandshakeSuccessful:
            if self.wait_for_packet():
                if Packet.unpack_packet(self._ReceivedPacket).getHeader().getFlags().flag_to_int() == 4:
                    print("test")
                    Syn_packet_bytes = self._ReceivedPacket
                    if self._btcpsocket.CheckChecksum(Syn_packet_bytes):
                        flags = Flags(1,1,0)
                        print(Syn_packet_bytes)
                        Syn_packet = Packet.unpack_packet(Syn_packet_bytes)
                        print(Syn_packet.getHeader().getSynNumber())
                        ack_number = Syn_packet.getHeader().getSynNumber() + 1
                        header = Header(random.getrandbits(15) & 0xffff, ack_number, flags, self._window, 0, 0)
                        Syn_Ack_packet = Packet(header, "syn_ack")
                        self._ReceivedPacket = None
                        self._lossy_layer.send_segment(Syn_Ack_packet.pack_packet())
                        if self.wait_for_packet():
                            if Packet.unpack_packet(self._ReceivedPacket).getHeader().getFlags().flag_to_int() == 2:
                                Ack_packet_bytes = self._ReceivedPacket
                                if self._btcpsocket.CheckChecksum(Ack_packet_bytes):
                                    print(Ack_packet_bytes)
                                    print(Packet.unpack_packet(Ack_packet_bytes))
                                    self._HandshakeSuccessful = True
                                    print("Handshake succesful")

    def wait_for_packet(self):
        timeNow = time.time()
        while self._ReceivedPacket is None and time.time() < timeNow + self._timeout*0.001:
            time.sleep(0.001)
        if self._ReceivedPacket is None:
            return False
        else:
            return True

    # Send any incoming data to the application layer
    def recv(self):
        packets = []
        for i in range(2, len(self._PacketList)):
            packet = Packet.unpack_packet(self._PacketList[i])
            Ack_number = packet.getHeader().getSynNumber() + packet.getHeader().getDatalength()
            header = Header(0, Ack_number, Flags(0,1,0), self._window, 0, 0)
            AckPacket = Packet(header, "")
            AckPacket_bytes = AckPacket.pack_packet()
            self._lossy_layer.send_segment(AckPacket_bytes)
            print(Packet.unpack_packet(self._PacketList[i]))

    # Clean up any state
    def close(self):
        self._ReceivedPacket = None
        if self.wait_for_packet():
            if Packet.unpack_packet(self._ReceivedPacket).getHeader().getFlags().flag_to_int() == 1:
                Fin_packet_bytes = self._ReceivedPacket
                if self._btcpsocket.CheckChecksum(Fin_packet_bytes):
                    flags = Flags(0, 1, 1)
                    print(Fin_packet_bytes)
                    Fin_packet = Packet.unpack_packet(Fin_packet_bytes)
                    print(Fin_packet)
                    print(Fin_packet.getHeader().getSynNumber())
                    ack_number = Fin_packet.getHeader().getSynNumber() + 1
                    header = Header(random.getrandbits(15) & 0xffff, ack_number, flags, self._window, 0, 0)
                    Fin_Ack_packet = Packet(header, "fin_ack")
                    self._ReceivedPacket = None
                    self._lossy_layer.send_segment(Fin_Ack_packet.pack_packet())
                    if self.wait_for_packet():
                        if Packet.unpack_packet(self._ReceivedPacket).getHeader().getFlags().flag_to_int() == 2:
                            Ack_packet_bytes = self._ReceivedPacket
                            print(Ack_packet_bytes)
                            print(Packet.unpack_packet(Ack_packet_bytes))
                            self._Disconnected = True
                            print("Disconnection succesful")
                            #self._lossy_layer.destroy()


    def packet_to_file(self, file):
        content = ""
        for i in range(2, len(self._PacketList)):
            content += Packet.unpack_packet(self._PacketList[i]).getPayload().decode()

        f = open(file, 'w')
        f.write(content)