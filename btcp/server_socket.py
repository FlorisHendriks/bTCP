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
        self._HandshakeSuccessful = False
        self._Disconnected = False
        self._PacketList = []
        self._OutputList = []
        self._PacketCounter = 0
        self._AckNumber = 0


    # Called by the lossy layer from another thread whenever a segment arrives
    def lossy_layer_input(self, segment):
        #print(segment)
        packet_bytes, address = segment
        self._PacketList.append(packet_bytes)
        self._ReceivedPacket = packet_bytes
        self._PacketCounter += 1
        pass

    # Wait for the client to initiate a three-way handshake
    def accept(self):
        print("Trying handshake")
        while not self._HandshakeSuccessful:
            self._PacketList = []
            self.wait_for_packet()
            Syn_packet_bytes = self._PacketList[0]
            Syn_packet = Packet.unpack_packet(Syn_packet_bytes)
            self._PacketList.pop(0)
            print("Syn Packet:")
            print(Syn_packet)
            if Syn_packet.getHeader().getFlags().flag_to_int() == 4 and self._btcpsocket.CheckChecksum(Syn_packet_bytes):
                #self._PacketList = []
                flags = Flags(1,1,0)
                print(Syn_packet_bytes)
                print(Syn_packet.getHeader().getSynNumber())
                ack_number = Syn_packet.getHeader().getSynNumber() + 1
                header = Header(random.getrandbits(15) & 0xffff, ack_number, flags, self._window, 0, 0)
                Syn_Ack_packet = Packet(header, "")
                Syn_Ack_packet_bytes = Syn_Ack_packet.pack_packet()
                self._AckNumber = ack_number
                self._lossy_layer.send_segment(Syn_Ack_packet_bytes)
                self.wait_for_packet()
                Ack_packet_bytes = self._PacketList[0]
                Ack_packet = Packet.unpack_packet(Ack_packet_bytes)
                self._PacketList.pop(0)
                print(Ack_packet.getHeader().getFlags().flag_to_int())
                if Ack_packet.getHeader().getFlags().flag_to_int() == 2:
                    if self._btcpsocket.CheckChecksum(Ack_packet_bytes):
                            self._HandshakeSuccessful = True
                            print("Server handshake successful")
                    else:
                        print("Ack packet checksum incorrect")
                else:
                    print("hallo2")
                    while not self._HandshakeSuccessful:
                        self._lossy_layer.send_segment(Syn_Ack_packet_bytes)
                        self.wait_for_packet()
                        packet = Packet.unpack_packet(self._PacketList[0])
                        self._PacketList.pop(0)
                        print("hallo")
                        print(packet)
                        if packet.getHeader().getFlags().flag_to_int() == 2:
                            if self._btcpsocket.CheckChecksum(packet.pack_packet()):
                                self._HandshakeSuccessful = True
                                print("Server handshake successful")
            else:
                print("packet timeout")

    def wait_for_packet(self):
        while not self._PacketList:
            time.sleep(0.001)

    # Send any incoming data to the application layer
    def recv(self):
        self.wait_for_packet()
        print(self._PacketList[0])
        while not Packet.unpack_packet(self._PacketList[0]).getHeader().getFlags().flag_to_int() == 1:
            packet = Packet.unpack_packet(self._PacketList[0])
            if packet.getHeader().getSynNumber() == self._AckNumber:
                self._AckNumber += packet.getHeader().getDatalength()
                header = Header(0, self._AckNumber, Flags(0,1,0), self._window, 0, 0)
                AckPacket = Packet(header, "")
                AckPacket_bytes = AckPacket.pack_packet()
                self._lossy_layer.send_segment(AckPacket_bytes)
                self._OutputList.append(self._PacketList[0])
                self._PacketList.pop(0)
                self.wait_for_packet()
            else:
                header = Header(0, self._AckNumber, Flags(0, 1, 0), self._window, 0, 0)
                AckPacket = Packet(header, "")
                AckPacket_bytes = AckPacket.pack_packet()
                self._lossy_layer.send_segment(AckPacket_bytes)
                self._PacketList.pop(0)
                self.wait_for_packet()
            print("server acknumber:")
            print(self._AckNumber)
    # Clean up any state
    def disconnect(self):
        print("Trying to disconnect:")
        Fin_packet_bytes = self._PacketList[0]
        self._PacketList.pop(0)
        if Packet.unpack_packet(Fin_packet_bytes).getHeader().getFlags().flag_to_int() == 1:
            if self._btcpsocket.CheckChecksum(Fin_packet_bytes):
                flags = Flags(0, 1, 1)
                print(Fin_packet_bytes)
                Fin_packet = Packet.unpack_packet(Fin_packet_bytes)
                print(Fin_packet)
                print(Fin_packet.getHeader().getSynNumber())
                ack_number = Fin_packet.getHeader().getSynNumber() + 1
                header = Header(random.getrandbits(15) & 0xffff, ack_number, flags, self._window, 0, 0)
                Fin_Ack_packet = Packet(header, "fin_ack")
                self._lossy_layer.send_segment(Fin_Ack_packet.pack_packet())
                self.wait_for_packet()
                Ack_packet_bytes = self._PacketList[0]
                self._PacketList.pop(0)
                if Packet.unpack_packet(Ack_packet_bytes).getHeader().getFlags().flag_to_int() == 2:
                    print(Ack_packet_bytes)
                    print(Packet.unpack_packet(Ack_packet_bytes))
                    self._Disconnected = True
                    print("Server disconnection successful")

    def packet_to_file(self, file):
        content = ""
        print("hallo3")
        print(len(self._OutputList))
        for i in range(0, len(self._OutputList)):
            content += Packet.unpack_packet(self._OutputList[i]).getPayload().decode()

        f = open(file, 'w')
        f.write(content)
        f.flush()
        f.close()


    def close(self):
        self._lossy_layer.destroy()

