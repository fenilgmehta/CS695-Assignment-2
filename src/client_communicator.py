import json
import os
import signal
import sys


def signal_handler(sig, frame):
    # REFER: https://stackoverflow.com/questions/1112343/how-do-i-capture-sigint-in-python
    print('\n\nYou pressed Ctrl+C ! Exiting...\n')
    sys.exit(0)


def interactive_client_communicator(client_fifo_file_name: str):
    # fifo_file_obj = open(client_fifo_file_name, 'a')
    try:
        while user_input := input("Enter your client manipulation command: "):
            os.system(f"echo '{user_input}' >> '{client_fifo_file_name}'")
            # fifo_file_obj.write(user_input)
            # fifo_file_obj.flush()
            ### with open(client_fifo_file_name, 'a') as my_file:
            ###     my_file.write(f'{user_input}\n')
            ###     my_file.flush()
    except EOFError:
        pass  # The use pressed CTRL+D
    return


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)

    fifo_file_name = json.load(open('client.conf', 'r'))['fifo_communication_file']
    interactive_client_communicator(fifo_file_name)
