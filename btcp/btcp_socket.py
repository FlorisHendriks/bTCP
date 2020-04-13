class BTCPSocket:
    def __init__(self, window, timeout):
        self._window = window
        self._timeout = timeout

    # Return the Internet checksum of data
    @staticmethod
    def in_cksum(packet_bytes):
        # We could not generalize this code in a for loop because 16 bits are in little-endian
        # (such as the sequence number and the acknowledgment number) and 8 bits are in big-endian (flags and window)
        checksum = 0
        byte = []
        byte.append(packet_bytes[0] + (packet_bytes[1] << 8))
        byte.append(packet_bytes[2] + (packet_bytes[3] << 8))
        byte.append(packet_bytes[4] & 0xffff)
        byte.append(packet_bytes[5] & 0xffff)
        for i in range(6, len(packet_bytes), 2):
            byte.append(packet_bytes[i] + (packet_bytes[i+1] << 8))
        for i in range(0, len(byte)):
            temp = checksum + byte[i]
            checksum = (temp & 0xffff) + (temp >> 16)

        checksum = ~checksum & 0xffff
        print("{0:016b}".format(checksum))
        return checksum
