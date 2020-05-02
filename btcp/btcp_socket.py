class BTCPSocket:
    def __init__(self, window, timeout):
        self._window = window
        self._timeout = timeout

    # Return the Internet checksum of data
    @staticmethod
    def in_cksum(data_bytes):
        # We could not generalize this code in one for loop because 16 bits are in little-endian
        # (such as the sequence number and the acknowledgment number) and 8 bits are in big-endian (flags and window)
        checksum = 0
        byte = []
        byte.append(data_bytes[0] + (data_bytes[1] << 8))
        byte.append(data_bytes[2] + (data_bytes[3] << 8))
        byte.append(data_bytes[4] & 0xffff)
        byte.append(data_bytes[5] & 0xffff)
        for i in range(6, len(data_bytes), 2):
            byte.append(data_bytes[i] + (data_bytes[i+1] << 8))
        for i in range(0, len(byte)):
            temp = checksum + byte[i]
            checksum = (temp & 0xffff) + (temp >> 16)

        checksum = ~checksum & 0xffff
        return checksum

    def CheckChecksum(packet):
        if int(BTCPSocket.in_cksum(packet)) == 0:
            return True
        else:
            return False
