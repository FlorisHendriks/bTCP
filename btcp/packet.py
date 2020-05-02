import struct
from btcp.btcp_socket import *

class Header:
    def __init__(self, Syn_number, Ack_number, flags, Window, Data_length, Checksum,):
        self._Syn_number = Syn_number
        self._Ack_number = Ack_number
        self._Flags = flags
        self._Window = Window
        self._Data_length = Data_length
        self._Checksum = Checksum

    def pack_header(self):
        return struct.pack('HHBBHH', self._Syn_number, self._Ack_number, self._Flags.flag_to_int(), self._Window, self._Data_length, self._Checksum)

    def unpack_header(packed_header):
        Syn_number, Ack_number, FlagInt, Window, Data_length, Checksum = struct.unpack('HHBBHH', packed_header)
        Flag = Flags.int_to_flag(FlagInt)
        return Header(Syn_number, Ack_number, Flag, Window, Data_length, Checksum)

    # Getting the protected attributes of the class
    def getSynNumber(self):
        return self._Syn_number

    def getAckNumber(self):
        return self._Ack_number

    def getFlags(self):
        return self._Flags

    def getWindow(self):
        return self._Window

    def getChecksum(self):
        return self._Checksum

    def getDatalength(self):
        return self._Data_length

    def __str__(self):
        return "Sequence number: " + str(self._Syn_number) + "\n" \
               + "Acknowledgment number: " + str(self._Ack_number) + "\n" \
               + "Flags: " + str(self._Flags) + "\n" \
               + "Window: " + str(self._Window) + "\n" \
               + "Data length: " + str(self._Data_length) + "\n" \
               + "Checksum: " + str(self._Checksum)

    def changeChecksum(self, checksum):
        self._Checksum = checksum

    def changeDataLength(self, DataLength):
        self._Data_length = DataLength


class Packet:
    def __init__(self, header, data):
        self._header = header
        self._payload = data.encode()
        self._padding = bytes(1008 - len(self._payload))

    # Convert the packet object to bytes, calculate the checksum, add it to the packet and finally return the
    # packet as bytes
    def pack_packet(self):
        self._header.changeDataLength(len(self._payload))
        packet_bytes = self._header.pack_header() + self._payload + self._padding
        checksum = BTCPSocket.in_cksum(packet_bytes)
        self._header.changeChecksum(checksum)
        return self._header.pack_header() + self._payload + self._padding

    # Convert the bytes to a packet object
    def unpack_packet(packed_packet):
        header = Header.unpack_header(packed_packet[:10])

        return Packet(header, packed_packet[10:header.getDatalength() + 10].decode())

    # Getting the protected attributes of the class
    def getHeader(self):
        return self._header

    def getPayload(self):
        return self._payload

    def getPadding(self):
        return self._padding

    def __str__(self):
        return "Header: " + str(self._header) + "\n" + "Payload: " + self._payload.decode()


class Flags:
    def __init__(self, syn, ack, fin):

        self._syn = syn
        self._ack = ack
        self._fin = fin

    def flag_to_int(self):
        integer = self._syn * 4 + self._ack * 2 + self._fin
        return integer

    def int_to_flag(flag_int):
        flags_string = "{0:03b}".format(flag_int)
        syn, ack, fin = int(flags_string[0]), int(flags_string[1]), int(flags_string[2])
        return Flags(syn, ack, fin)

    def __str__(self):
        return "syn: " + str(self._syn) + " " + "ack: " + str(self._ack) + " " + "fin: " + str(self._fin)
