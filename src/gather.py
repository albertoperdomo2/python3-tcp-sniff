import argparse
import socket
import sys
import logging
import requests
import time

from multiprocessing import Process, Queue
from struct import *

FORMAT ='[ %(levelname)s ] - %(asctime)s : %(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
logger = logging.getLogger(__name__)

class gatherTCP():
    """Class to create a TCP/IP gathering object.

    Args:
        url: main server to send the sniffed data.
    """
    def __init__(self, url):
        self.url = url

    def run(self):
        """Method to create both the sniffing and the http client processes.
        It initializes the queue object too.
        """
        logger.info("starting service...")
        queue = Queue()

        sniffing_proc = Process(target=self._sniff_data, args=(queue,))
        httpclient_proc = Process(target=self._http_client, args=(queue,))

        sniffing_proc.start()
        httpclient_proc.start()

        sniffing_proc.join()
        httpclient_proc.join()

    def _sniff_data(self, queue):
        """Function to run the data sniffing process.
        A raw socket is created, then the bytes are read from the TCP socket and unpacked to get the data field.

        Args:
            queue: multiprocessing.Queue object to dump the data.
        """
        try:
            logger.debug("creating new raw socket.")
            _socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(0x0003)) # socket.ntohs(0x0003) means all packages, be careful
        except socket.error:
            logger.error("socket could not be created!")
            sys.exit()

        logger.debug("starting sniffing process.")
        while True:
            packet = _socket.recvfrom(65565) # the IP header has a 16 bit section for header length (2^16 = 65536)
            packet = packet[0] # get the packet string from tuple

            # parse ethernet header
            eth_length = 14
            eth_header = packet[:eth_length]
            eth = unpack('!6s6sH' , eth_header)
            # unpack format: !6s6sH means is Big Endian byte order, H = unsigned short, and 6s = char[6]
            eth_protocol = socket.ntohs(eth[2]) # convert 16 bit integer from network format to host format

            # parse IP packets (protocol nr 8)
            if eth_protocol == 8:
                ip_header = unpack('!BBHHHBBH4s4s' , packet[eth_length:20+eth_length]) # unpack the ip header (20 bytes from eth header) 
                # unpack format: !BBHHHBBH4s4s means is Big Endian byte order, B = unsigned char, H = unsigned short, and 4s = char[4]

                version_ihl = ip_header[0]
                # version = version_ihl >> 4 
                ihl = version_ihl & 0xF # bitwise AND with 0b00001111 (15), which discards the 4 most significant bits, leaving the 4 least significant bits (i.e. header length)
                iph_length = ihl * 4

                protocol = ip_header[6]

                # analyze each protocol ()
                if protocol == 6: # TCP
                    tcph_start = iph_length + eth_length # start point of the TCP header
                    tcph = unpack('!HHLLBBHHH' , packet[tcph_start:tcph_start+20]) # unpack the TCP header
                    # unpack format: !BBHHHBBH4s4s means is Big Endian byte order, B = unsigned char, H = unsigned short, and L = unsigned long

                    doff_reserved = tcph[4] # data offset
                    tcph_length = doff_reserved >> 4 # get the header length from the data offset (32 bit word)

                    h_size = eth_length + iph_length + tcph_length * 4 # total header size

                    # get data from the packet
                    data = packet[h_size:]
                    logger.debug(f"DATA: {str(data)}")
                    queue.put(data.decode('unicode_escape')) # TODO: I am not sure how to decode/encode this data.
    
    def _http_client(self, queue):
        """Function to run the POST requests.
        It sleeps for 300 seconds (5 minutes) before reading the data from the queue and making the POST request.

        Args:
            queue: multiprocessing.Queue object to dump the data.
        """
        logger.debug(f"dst URL {self.url}")
        while True:
            time.sleep(300) # sleep for 5 minutes before POSTing
            if not queue.empty():
                res = requests.post(self.url, data={b'data': queue.get()}) # TODO: I'm not sure either how to decode it before sending it
                if not res.ok:
                    logger.warning(f"HTTP RESPONSE NOK: {res.content}")

def get_args_parser():
    """Function to parse the argument of the CLI.
    """
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument(
        '--url',
        help="URL of the main server (where to post the data).",
        default="http://0.0.0.0:8000/",
    )
    args_parser.add_argument(
        '-v', '--verbose',
        help="verbose output. Specify twice for debug level verbosity.",
        dest='verbose',
        action='count',
        default=0
    )

    return args_parser

if __name__ == '__main__':
    args = get_args_parser().parse_args()

    if args.verbose > 1:
        logger.setLevel(logging.DEBUG)
    elif args.verbose > 0:
        logger.setLevel(logging.INFO)

    tcp_gatherer = gatherTCP(url=args.url)
    tcp_gatherer.run()

