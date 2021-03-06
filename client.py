import signal
import struct
import os
import json
import logging
import sys
import socket
import fcntl
import sys
import time
import random
import threading
import pprint


def make_fd_non_blocking(file_fd):
    """
    make file_fd a non-blocking file descriptor
    """
    # REFER: https://stackoverflow.com/questions/375427/a-non-blocking-read-on-a-subprocess-pipe-in-python
    fl = fcntl.fcntl(file_fd, fcntl.F_GETFL)
    fcntl.fcntl(file_fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)


def handle_input(user_input, client_conf):
    user_input = user_input.strip()
    if len(user_input) == 0:
        return
    logging.debug(f'len(user_input) = {len(user_input)}')
    logging.debug(f'user_input = "{user_input}"')
    input_parts = user_input.split()
    if input_parts[0] == '-':
        # remove the server from list
        try:
            logging.debug(client_conf['server_address_port'])
            logging.debug(input_parts)
            logging.debug([(input_parts[1], int(input_parts[2]),)])
            client_conf['server_address_port'].remove(
                (input_parts[1], int(input_parts[2]),)
            )
        except ValueError:
            logging.debug('Removal of server failed')
    elif input_parts[0] == '+':
        # add the server to the list
        client_conf['server_address_port'].append((input_parts[1], int(input_parts[2])))
    elif input_parts[0] == 'low':
        client_conf['req_load'] = 'low'
    elif input_parts[0] == 'high':
        client_conf['req_load'] = 'high'
    else:
        logging.warning(f'Incorrect user_input = "{user_input}"')
    return


def start_sending_requests(client_conf, message_conf) -> None:
    logging.debug('start_sending_requests(...) STARTED :)')
    client_conf['server_address_port'] = [(client_conf['server_ip'], int(client_conf['server_port']))]

    # Create a UDP socket
    udp_client_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

    # NOTE: bind is optional for client

    # https://stackoverflow.com/questions/25426447/creating-non-blocking-socket-in-python
    udp_client_socket.setblocking(False)

    while True:
        # Check if there is any change in the list of servers IP and port list or not
        try:
            user_input = client_conf['fifo_communication_file_obj'].readline()
            logging.debug(f'user_input = "{user_input}"')
            handle_input(user_input, client_conf)
        except Exception as e:
            logging.critical(f'Inside "except" clause for "user_input", type(e)={type(e)}, str(e)={str(e)}')

        if len(client_conf['server_address_port']) == 0:
            logging.debug('Total servers = len(client_conf[\'server_address_port\']) = 0')
        for server_i in client_conf['server_address_port']:
            # Generate Random query
            req_int = random.randint(client_conf['req_num_low'], client_conf['req_num_high'])

            # Format: big-endian and 4 bytes (unsigned int)
            req_bytes_to_send = struct.pack(">I", req_int)  # max value can be "2**32 - 1"
            logging.debug(f'Query:')
            logging.debug(f'    req_int           = {req_int}')
            logging.debug(f'    req_bytes_to_send = {req_bytes_to_send}')

            # Send to server using created UDP socket
            udp_client_socket.sendto(req_bytes_to_send, server_i)

        # Receive all server replies without blocking
        # Format: big-endian and 8 bytes (unsigned long long)
        try:
            while True:
                req_reply_bytes, server_addr = udp_client_socket.recvfrom(8)
                logging.debug(f'Response of server_addr = {server_addr}')
                logging.debug(f'    req_reply_bytes = {req_reply_bytes}')
                req_reply_int = int.from_bytes(req_reply_bytes, 'big')
                logging.debug(f'    req_reply_int   = {req_reply_int}')
        except BlockingIOError:
            pass  # nothing to receive
        except Exception as e:
            logging.debug(f'type(e) = {type(e)}')
            logging.debug(f'e = {e}')

        if client_conf['req_load'] == 'low':
            time.sleep(1.3)
            pass
        elif client_conf['req_load'] == 'high':
            time.sleep(0.7)
            pass
        else:
            logging.critical('Wrong value stored in "client_conf[\'req_load\']"')
    # noinspection PyUnreachableCode
    logging.debug('start_sending_requests(...) ENDED - this will never execute')
    pass


def client_init(client_conf: dict):
    logging.basicConfig(
        level=eval(f'logging.{client_conf["logging_level"]}'),
        stream=(open(client_conf['logging_file'], 'a') if client_conf['logging_file'] != '/dev/stdout' else sys.stdout),
        format='%(asctime)s :: %(levelname)s :: %(lineno)s :: %(funcName)s :: %(message)s'
    )

    problem_with_fifo = False
    if client_conf['fifo_communication_file'] != '/dev/stdin':
        try:
            # REFER: https://stackoverflow.com/questions/1430446/create-a-temporary-fifo-named-pipe-in-python
            os.mkfifo(client_conf['fifo_communication_file'])
            logging.info(f'File used for communication = "{client_conf["fifo_communication_file"]}"')
            # REFER: https://github.com/pahaz/cryptoassets/blob/master/cryptoassets/core/backend/pipewalletnotify.py#L140
            # REFER: https://stackoverflow.com/questions/168559/python-how-do-i-convert-an-os-level-handle-to-an-open-file-to-a-file-object
            # client_conf['fifo_communication_file_obj'] = os.fdopen(
            #     os.open(client_conf['fifo_communication_file'], os.O_RDONLY | os.O_NONBLOCK),
            #     'rt'
            # )
            client_conf['fifo_communication_file_obj'] = open(client_conf['fifo_communication_file'])
            logging.info('FIFO file successfully opened :)')
        except OSError as e:
            logging.warning(f'Failed to create FIFO: {e}')
            problem_with_fifo = True

    if problem_with_fifo or client_conf['fifo_communication_file'] == '/dev/stdin':
        client_conf['fifo_communication_file'] = '/dev/stdin'
        client_conf['fifo_communication_file_obj'] = sys.stdin
        logging.info(f'File used for communication = "/dev/stdin"')

    # https://www.tutorialspoint.com/python/file_fileno.htm
    make_fd_non_blocking(client_conf['fifo_communication_file_obj'].fileno())
    logging.debug('client_init() FINISHED :)')
    return


GLOBAL_CLIENT_CONF = None


def signal_handler(sig, frame):
    # REFER: https://stackoverflow.com/questions/1112343/how-do-i-capture-sigint-in-python
    print('\n\nYou pressed Ctrl+C !\n')
    GLOBAL_CLIENT_CONF['fifo_communication_file_obj'].close()
    if GLOBAL_CLIENT_CONF['fifo_communication_file'] != '/dev/stdin':
        # https://www.w3schools.com/python/python_file_remove.asp
        os.remove(GLOBAL_CLIENT_CONF['fifo_communication_file'])
    logging.debug(f'Successfully deleted "{GLOBAL_CLIENT_CONF["fifo_communication_file"]}"')
    pprint.pprint(GLOBAL_CLIENT_CONF)
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)

    # load settings
    with open('message.conf') as f:
        MESSAGE_CONF = json.load(f)
    with open('client.conf') as f:
        CLIENT_CONF = json.load(f)

    # set settings
    client_init(CLIENT_CONF)
    GLOBAL_CLIENT_CONF = CLIENT_CONF

    start_sending_requests(CLIENT_CONF, MESSAGE_CONF)
