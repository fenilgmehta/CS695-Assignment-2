import logging
import random
import signal
import socket
import struct
import sys


def serve_request(n: int) -> int:
    a = (2 ** n)
    # 1021 is the largest prime smaller than 1024
    return a % 1021


def start_serving_requests(udp_port) -> None:
    sock: socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # NOTE: empty udp_host means that the socket should accept requests from all network interfaces
    # udp_host = socket.gethostname()
    udp_host = ''
    logging.debug(f"UDP Host = {udp_host}")
    logging.debug(f"UDP Port = {udp_port}")
    try:
        sock.bind((udp_host, udp_port))
    except OSError as e:
        # OSError: [Errno 98] Address already in use
        logging.debug(f'OSError e = {e}')
        udp_port = random.randint(udp_port + 1, udp_port + 20)
        sock.bind((udp_host, udp_port))
        logging.debug(f"NEW UDP Port = {udp_port}")
    except Exception as e:
        logging.warning(f'Exception e = {e}')

    print("Waiting for client requests...")
    while True:
        # Receive request
        client_data_bytes, client_addr = sock.recvfrom(4)  # receive data from client
        logging.debug(f"FROM: client_addr = {client_addr}")
        logging.debug(f"      type(data)        = {type(client_data_bytes)}")
        logging.debug(f"      client_data_bytes = {client_data_bytes}")

        client_data_int = int.from_bytes(client_data_bytes, "big")
        logging.debug(f"      client_data_int   = {client_data_int}")

        # Process the request
        # Response FORMAT: big-endian, 8 bytes, unsigned long long
        response = serve_request(client_data_int)
        logging.debug(f"      RESPONSE = {response}")

        # Send response/reply
        sock.sendto(struct.pack(">Q", response), client_addr)
    pass


def signal_handler(sig, frame):
    # REFER: https://stackoverflow.com/questions/1112343/how-do-i-capture-sigint-in-python
    print('\n\nYou pressed Ctrl+C !\n')
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)

    # load settings
    # with open('message.conf') as f:
    #     MESSAGE = json.load(f)
    # with open('server.conf') as f:
    #     SERVER_SETTINGS = json.load(f)
    SERVER_SETTINGS = {
        'logging_level': 'DEBUG',
        'logging_file': '/tmp/CS695-server.log',
        # 'logging_file': '/dev/stdout',
    }

    # set settings
    logging.basicConfig(
        level=eval(f"logging.{SERVER_SETTINGS['logging_level']}"),
        stream=(open(SERVER_SETTINGS['logging_file'], 'a')
                if SERVER_SETTINGS['logging_file'] != '/dev/stdout' else sys.stdout),
        format='%(asctime)s :: %(levelname)s :: %(lineno)s :: %(funcName)s :: %(message)s'
    )

    start_serving_requests(21001)
