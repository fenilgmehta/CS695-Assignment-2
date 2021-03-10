import logging
import os
import pprint
import socket
from typing import Dict, List

import libvirt
import matplotlib.pyplot as plt


def get_ip_address(domain_object: libvirt.virDomain) -> str:
    """:return: IPv4 address of the domain_object"""
    # REFER: https://github.com/libvirt/libvirt-python/blob/master/examples/domipaddrs.py#L15
    logging.debug(f'interfaceAddresses = '
                  f'{pprint.pformat(domain_object.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE))}')
    for i in domain_object.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE).values():
        return str(i['addrs'][0]['addr'])
    return 'None'
    # # Below solution did NOT work
    # # REFER: libvirt-domain: https://libvirt.org/html/libvirt-libvirt-domain.html#virDomainGetConnect
    # dom_connect: libvirt.virConnect = domain_object.connect()
    # # REFER: libvirt-network: https://libvirt.org/html/libvirt-libvirt-network.html
    # dom_networks: libvirt.virNetwork = dom_connect.listAllNetworks()
    # return dom_networks[0].DHCPLeases()[0]['ipaddr']


def get_ip_address_log(conn: libvirt.virConnect, network_name: str = 'default'):
    # REFER: https://stackoverflow.com/questions/19057915/libvirt-fetch-ipv4-address-from-guest
    for lease in conn.networkLookupByName(network_name).DHCPLeases():
        print(lease)


def get_active_servers_list(conn: libvirt.virConnect, domain_prefix: str, server_port: int) -> List[libvirt.virDomain]:
    active_server_domains: List[libvirt.virDomain] = list()
    active_server_ids: List = conn.listDomainsID()  # Only ONLINE domain ID's are returned
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    for i in active_server_ids:
        temp_domain: libvirt.virDomain = conn.lookupByID(i)
        temp_domain_name: str = temp_domain.name()
        if temp_domain_name.startswith(domain_prefix):
            try:
                if my_socket.connect_ex((get_ip_address(temp_domain), server_port)) == 0:
                    active_server_domains.append(temp_domain)
                else:
                    logging.debug(f'VM is up. But, the server program port is not open')
            except Exception as e:
                logging.warning(f'Unexpected EXCEPTION: {e}')
    active_server_domains: List[libvirt.virDomain] = [i for _, i in sorted(list(zip(
        [j.name() for j in active_server_domains],
        active_server_domains
    )), key=lambda pair: pair[0])]
    return active_server_domains


class ClientFIFO:
    """
    Currently supported functionalities:
        1. Add server syntax    = "+ <IP_ADDRESS> <PORT>"
        2. Remove server syntax = "- <IP_ADDRESS> <PORT>"
        3. Remove all servers   = "clear"
        4. Refresh the servers list = "refresh"
        5. Change client's request/query generation speed:
            a. low
            b. mid
            c. high
    """

    def __init__(self, fifo_file_object, server_program_port_number: int, fifo_file_name: str = None):
        """
        :param fifo_file_object: e.g. open('fifo', 'r'), open('fifo', 'a')
        """
        self.fifo_file_object = fifo_file_object
        self.server_program_port_number = server_program_port_number
        self.fifo_file_name = fifo_file_name

    def add_server(self, domain_object: libvirt.virDomain) -> None:
        # print(f'+ {get_ip_address(domain_object)} {self.server_program_port_number}', file=self.fifo_file_object)
        # os.system(f"echo '+ {get_ip_address(domain_object)} "
        #           f"{self.server_program_port_number}' >> '{self.fifo_file_name}'")
        self.add_server_ip(get_ip_address(domain_object))

    def add_server_ip(self, server_ip: str) -> None:
        if self.fifo_file_name is None:
            logging.critical('self.fifo_file_name is None')
        logging.debug(f'+ {server_ip} {self.server_program_port_number}')
        # print(f'+ {server_ip} {self.server_program_port_number}', file=self.fifo_file_object)
        os.system(f"echo '+ {server_ip} {self.server_program_port_number}' >> '{self.fifo_file_name}'")

    def remove_server(self, domain_object: libvirt.virDomain) -> None:
        if self.fifo_file_name is None:
            logging.critical('self.fifo_file_name is None')
        # print(f'- {get_ip_address(domain_object)} {self.server_program_port_number}', file=self.fifo_file_object)
        os.system(
            f"echo '- {get_ip_address(domain_object)} {self.server_program_port_number}' >> '{self.fifo_file_name}'")

    def clear_all_servers(self) -> None:
        if self.fifo_file_name is None:
            logging.critical('self.fifo_file_name is None')
        # print(f'clear_servers', file=self.fifo_file_object)
        os.system(f"echo 'clear_servers' >> '{self.fifo_file_name}'")

    def check_fifo(self, client_conf: Dict) -> None:
        # Check if there is any change in the list of servers IP and port list or not
        if self.fifo_file_object is None:
            logging.critical("self.fifo_file_object is None")
        try:
            user_input = self.fifo_file_object.readline()
            user_input = user_input.strip()
            if len(user_input) == 0:
                return
            ClientFIFO.__handle_input(user_input, client_conf)
        except Exception as e:
            logging.critical(f'Inside "except" clause for "user_input", type(e)={type(e)}, str(e)={str(e)}')
        pass

    @staticmethod
    def __handle_input(user_input: str, client_conf: Dict) -> None:
        # logging.debug(f'user_input = "{user_input}"')
        logging.debug(f'len(user_input) = {len(user_input)}')
        logging.debug(f'user_input      = "{user_input}"')
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
                logging.info('Removal of server failed')
        elif input_parts[0] == '+':
            # add the server to the list
            # if (input_parts[1], int(input_parts[2])) not in client_conf['server_address_port']:
            logging.debug(f'client_conf["server_address_port"] = {client_conf["server_address_port"]}')
            if (input_parts[1], int(input_parts[2])) in client_conf['server_address_port']:
                logging.debug(f'VM not added to the servers list = {(input_parts[1], int(input_parts[2]))}')
            else:
                client_conf['server_address_port'].append((input_parts[1], int(input_parts[2])))
        elif input_parts[0] == 'clear_servers':
            client_conf['server_address_port'].clear()
        elif input_parts[0] == 'refresh':
            client_conf['server_address_port'] = get_active_servers_list(
                libvirt.open('qemu:///system'),
                client_conf['auto_scaler_domain_prefix'],
                client_conf['server_port']
            )
            client_conf['server_address_port'] = [
                (get_ip_address(i), client_conf["server_port"]) for i in client_conf['server_address_port']
            ]
        elif input_parts[0].lower() in ('low', 'mid', 'high'):
            client_conf['req_load'] = input_parts[0].lower()
        elif input_parts[0] == 'custom':
            if len(input_parts) > 1:
                client_conf['req_load'] = 'custom'
                client_conf['load_request_time_period_seconds_custom'] = float(input_parts[1])
            else:
                logging.warning(f'Time period not mentioned req_load = "custom", input_parts = "{input_parts}"')
        else:
            logging.warning(f'Incorrect user_input = "{user_input}"')
        return


def shift_left_and_add(arr, new_val):
    arr[:-1] = arr[1:]
    arr[-1] = new_val


# REFER: https://stackoverflow.com/questions/10944621/dynamically-updating-plot-in-matplotlib
class DynamicUpdate:
    # Suppose we know the x range
    def __init__(self, min_x, max_x, min_y, max_y, label_x=None, label_y=None):
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y
        self.label_x = label_x
        self.label_y = label_y

    def on_launch(self):
        plt.ion()

        # Set up plot
        self.figure, self.ax = plt.subplots()

        # self.lines, = self.ax.plot([],[], 'o')  # Scatter plot
        self.lines = [self.ax.plot([], [])[0]]  # Line plot

        # Autoscale on unknown axis and known lims on the other
        self.ax.set_autoscaley_on(True)
        self.ax.set_xlim(self.min_x, self.max_x)
        self.ax.set_ylim(self.min_y, self.max_y)

        if self.label_x is not None:
            self.ax.set_xlabel(self.label_x)
        if self.label_y is not None:
            self.ax.set_ylabel(self.label_y)

        # Other stuff
        self.ax.grid()

    def on_running(self, xdata, ydata, line_idx=0):
        if xdata is None and ydata is None:
            return

        if line_idx == len(self.lines):
            # REFER: https://www.geeksforgeeks.org/line-chart-in-matplotlib-python/
            self.lines.append(self.ax.plot([], [])[0])

        # Update data (with the new _and_ the old points)
        self.lines[line_idx].set_xdata(xdata)
        self.lines[line_idx].set_ydata(ydata)

        # # Need both of these in order to rescale
        # self.ax.relim()
        # self.ax.autoscale_view()

        # We need to draw *and* flush
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()

    # Example
    def __call__(self):
        import numpy as np
        import time
        self.on_launch()
        xdata = []
        ydata = []
        for x in np.arange(0, 10, 0.5):
            xdata.append(x)
            ydata.append(np.exp(-x ** 2) + 10 * np.exp(-(x - 7) ** 2))
            self.on_running(xdata, ydata)
            time.sleep(1)
        return xdata, ydata


if __name__ == '__main__':
    d = DynamicUpdate(0, 10, 0, 10)
    # d()
    d.on_launch()
    xdata = 5 * [None]
    ydata = 5 * [None]
    shift_left_and_add(xdata, 1)
    shift_left_and_add(ydata, 2)
    d.on_running(xdata, ydata)
