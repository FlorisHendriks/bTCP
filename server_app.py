#!/usr/local/bin/python3

import argparse
from btcp.server_socket import BTCPServerSocket
import threading
import os


class TCPServer(threading.Thread):
    def run(self):
        self.main()

    @staticmethod
    def main():
        parser = argparse.ArgumentParser()
        parser.add_argument("-w", "--window", help="Define bTCP window size", type=int, default=100)
        parser.add_argument("-t", "--timeout", help="Define bTCP timeout in milliseconds", type=int, default=100)
        parser.add_argument("-o", "--output", help="Where to store the file", default="output.file")
        args = parser.parse_args()

        # Create a bTCP server socket
        s = BTCPServerSocket(args.window, args.timeout)

        s.accept()
        s.recv()
        s.packet_to_file(args.output)

        s.disconnect()
        # Clean up any state
        s.close()

    @staticmethod
    def remove_file(outputfile):
        if os.path.isfile(outputfile):
            os.remove(outputfile)
