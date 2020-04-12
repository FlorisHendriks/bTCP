class BTCPSocket:
    def __init__(self, window, timeout):
        self._window = window
        self._timeout = timeout

    # Return the Internet checksum of data
    @staticmethod
    def in_cksum(packet_bytes):
        checksum = 0
        byte = packet_bytes[0] + packet_bytes[i + 1] >> 8
        checksum += byte

        checksum = checksum + (checksum >> 16)
        checksum = ~checksum & 0xffff
        print("{0:016b}".format(checksum))
        return checksum
