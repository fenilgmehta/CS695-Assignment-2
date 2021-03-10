import copy
import json
import logging
import signal
import socket
import sys
import time
from pprint import pprint
from typing import List, Dict

import libvirt
import numpy as np

import client_common_services as cs

# REFER: https://stackoverflow.com/questions/35325042/python-logging-disable-logging-from-imported-modules
logger = logging.getLogger('auto_scaler.py')


def all_equals(my_list: List[int], val) -> bool:
    res = True
    for i in my_list:
        res = res and (i == val)
    return res


def get_cpu_usage(domain_obj: libvirt.virDomain, sleep_time: int = 1) -> float:
    """
    REFER: https://stackoverflow.com/questions/40468370/what-does-cpu-time-represent-exactly-in-libvirt
    :param domain_obj:
    :param sleep_time: The difference in time interval in SECONDS after
                       the 1st time CPU stats are fetched and
                       the 2nd time CPU stats are to be fetched
    :return: Percentage of CPU usage
    """
    # The time values returned by "getCPUStats" is in nanoseconds
    cpu_stat_1 = domain_obj.getCPUStats(True)[0]
    time.sleep(sleep_time)
    cpu_stat_2 = domain_obj.getCPUStats(True)[0]
    cpu_percent = 100 * ((cpu_stat_2['cpu_time'] - cpu_stat_1['cpu_time']) / 1000000000) / sleep_time
    domain_cpu_cores = len(domain_obj.vcpus()[0])
    return cpu_percent / domain_cpu_cores


def pool_server_for_use(new_domain_obj: libvirt.virDomain, client_fifo: cs.ClientFIFO, server_up_time: int):
    # server_ip: str
    # get_ip_address(new_domain_obj)
    while (server_ip := cs.get_ip_address(new_domain_obj)) == 'None':
        logger.debug(f'server_ip = {server_ip}')
        time.sleep(1)

    # "socket.SOCK_DGRAM" is for UDP connection
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        try:
            logger.debug(f'server_ip = {server_ip}')
            logger.debug(f'client_fifo.server_program_port_number = {client_fifo.server_program_port_number}')
            if my_socket.connect_ex((server_ip, client_fifo.server_program_port_number)) == 0:
                # Port is open => Server VM has started
                logger.info(f'Going to sleep for server_up_time = "{server_up_time}"')
                time.sleep(server_up_time)
                client_fifo.add_server_ip(server_ip)
                logger.info('THREAD: Successfully informed the client :)')
                my_socket.close()
                return
            logger.debug(
                f'connection test result = {my_socket.connect_ex((server_ip, client_fifo.server_program_port_number))}'
            )
        except Exception as e:
            logger.warning(f'Unexpected Exception: {type(e)} ---> {e}')
        time.sleep(1)
    pass


def run_autoscaler(client_conf: Dict, initially_add_running_servers: bool) -> None:
    """
    Important Assumption: there is at least one Server VM running before
                          the execution of this function starts,
                          AND, the VM's have the server program running.
    :param client_conf: dictionary of "client.conf" file
    :return: None
    """
    logger.setLevel(eval(f'logging.{client_conf["logging_level"]}'))
    logging.basicConfig(
        # level=eval(f'logging.{client_conf["logging_level"]}'),
        stream=(open(client_conf['logging_file'], 'a') if client_conf['logging_file'] != '/dev/stdout' else sys.stdout),
        format='%(asctime)s :: %(levelname)s :: %(lineno)s :: %(funcName)s :: %(message)s'
    )

    logger.info("auto_scaler: INITIALIZATION STARTS")
    domain_prefix: str = client_conf['auto_scaler_domain_prefix']
    auto_scaler_vm_num_digits: int = client_conf['auto_scaler_vm_num_digits']
    auto_scaler_load_minimum_seconds: int = client_conf['auto_scaler_load_minimum_seconds']
    client_fifo: cs.ClientFIFO = cs.ClientFIFO(None, client_conf['server_port'], client_conf['fifo_communication_file'])
    logger.info("auto_scaler: INITIALIZATION COMPLETE")

    conn = libvirt.open('qemu:///system')

    active_server_domains = cs.get_active_servers_list(conn, domain_prefix, client_conf['server_port'])
    logger.info(f'Detected running VM\'s = {[i.name() for i in active_server_domains]}')

    if initially_add_running_servers:
        logger.info(f'Informing the client about the server VM\'s')
        for i in active_server_domains:
            logger.debug(f'    Adding "{i.name()}"')
            client_fifo.add_server(i)

    if len(active_server_domains) == 0:
        logger.warning("len(active_server_domains) = 0")
        logger.warning("Exiting...")
        sys.exit(0)

    # 1 = low load / CPU utilization
    # 2 = mid load / CPU utilization
    # 3 = high load / CPU utilization
    cpu_low_high_mapper: List = [0] * auto_scaler_load_minimum_seconds
    mapper_idx: int = 0
    extra_old_time_data = client_conf['graph_history_seconds']  # seconds
    cpu_avg_load_x_default: np.array = np.array(
        list(range(0, (auto_scaler_load_minimum_seconds + extra_old_time_data) + 1))
    )
    cpu_avg_load_y_default: np.array = np.array([np.nan] * (auto_scaler_load_minimum_seconds + extra_old_time_data + 1))
    cpu_avg_load_y: List = [copy.deepcopy(cpu_avg_load_y_default)]
    updating_graph = cs.DynamicUpdate(min_x=0,
                                      max_x=(auto_scaler_load_minimum_seconds + extra_old_time_data),
                                      min_y=0,
                                      max_y=100,
                                      label_x="Time",
                                      label_y="CPU Usage")
    ### ticks_x_val_name=[str(i) for i in range(0, auto_scaler_load_minimum_seconds + extra_old_time_data + 1)],
    ### ticks_val_name=None,
    # updating_graph.ax.set_xticks(range(self.min_x, self.max_x + 1), self.ticks_x_val_name)
    # updating_graph.ax.set_yticks(range(self.min_y, self.max_y + 1), self.ticks_y_val_name)
    # updating_graph.ax.set_xticklabels(list(reversed(updating_graph.ax.get_xticks())))

    updating_graph.on_launch()
    # logger.debug(list(reversed(updating_graph.ax.get_xticks())))
    updating_graph.ax.set_xticks(list(range(0, extra_old_time_data+1, 10)))
    updating_graph.ax.set_xticklabels(list(reversed(range(0, extra_old_time_data+1, 10))))
    while True:
        logger.debug(f'cpu_low_high_mapper = {cpu_low_high_mapper}')
        logger.debug(f'                       {"   " * mapper_idx}^')
        cpu_use_percentage = list()
        down_server_idx = list()
        for i in range(len(active_server_domains)):
            try:
                cpu_use_percentage.append(get_cpu_usage(active_server_domains[i]))
            except libvirt.libvirtError as e:
                logger.critical(f'Running VM closed by someone :(  --->  {e}')
                down_server_idx.append(i)
        # Restart the servers which were turned off
        for i in down_server_idx:
            active_server_domains[i].create()

        cpu_use_percentage_average = sum(cpu_use_percentage) // len(active_server_domains)
        logger.debug(f'cpu_use_percentage (%)     = {[int(i) for i in cpu_use_percentage]}')
        logger.debug(f'cpu_use_percentage_average = {cpu_use_percentage_average} %')

        if all_equals(cpu_low_high_mapper, 1):
            # Constantly low load for "auto_scaler_load_minimum_seconds" amount of time
            # Hence stop one server VM if number of VM's > 1
            logger.info("past_n_seconds_avg_load = 1")
            if len(active_server_domains) > 1:
                domain_to_stop = active_server_domains.pop()
                client_fifo.remove_server(domain_to_stop)  # Inform the client
                time.sleep(1)
                domain_to_stop.shutdown()
                # domain_to_stop.destroy()  # Use this if above call does not work
                logger.info(f'Stopping the VM: "{domain_to_stop.name()}"')
            else:
                logger.info(
                    f'NOT Stopping any VM as only one is running: "{active_server_domains[0].name()}"'
                )
            pass
        elif all_equals(cpu_low_high_mapper, 3):
            # Constantly high load for "auto_scaler_load_minimum_seconds" amount of time
            # Hence spawn a new server VM
            logger.debug("past_n_seconds_avg_load = 3")
            try:
                new_domain_obj: libvirt.virDomain = conn.lookupByName(
                    f'{domain_prefix}{len(active_server_domains):0{auto_scaler_vm_num_digits}}'
                )
                active_server_domains.append(new_domain_obj)
                new_domain_obj.create()

                logger.info(f'New VM info')
                logger.info(f'    VM Name = "{new_domain_obj.name()}"')
                logger.info(f'    VM IP   = "{cs.get_ip_address(new_domain_obj)}"')
                # Inform the client
                # threading.Thread(target=pool_server_for_use, args=(get_ip_address(new_domain_obj), client_fifo)).start()
                pool_server_for_use(new_domain_obj, client_fifo, client_conf['server_up_time'])
            except libvirt.libvirtError as e:
                logger.debug(f'Ran out of VM\'s. No more ready VM\'s for use')
                logger.debug(f'ERROR creating new VM: libvirt.libvirtError: {e}')
            # Create a new VM using libvirt API
            # # REFER: https://libvirt.org/html/libvirt-libvirt-domain.html#virDomainGetXMLDesc
            # print(b.XMLDesc())
            # conn.createXML(active_server_domains[0].XMLDesc())
            # # REFER: https://libvirt.org/html/libvirt-libvirt-domain.html#virDomainCreateXML
            # ### REFER: https://libvirt.org/html/libvirt-libvirt-domain.html#virDomainDefineXML
            # ### REFER: https://libvirt.org/html/libvirt-libvirt-domain.html#virDomainCreate
            pass

        for i in range(len(cpu_use_percentage)):
            if i == len(cpu_avg_load_y):
                cpu_avg_load_y.append(copy.deepcopy(cpu_avg_load_y_default))
            cs.shift_left_and_add(cpu_avg_load_y[i], cpu_use_percentage[i])
        for i in range(len(cpu_use_percentage), len(cpu_avg_load_y)):
            cs.shift_left_and_add(cpu_avg_load_y[i], np.nan)
        # if mapper_idx % (auto_scaler_load_minimum_seconds) == 0:
        #     logger.debug(f'cpu_avg_load_y = {cpu_avg_load_y}')
        for i in range(len(cpu_avg_load_y)):
            updating_graph.on_running(xdata=cpu_avg_load_x_default, ydata=cpu_avg_load_y[i], line_idx=i)

        past_n_seconds_load_vals: List[int] = list(set(cpu_low_high_mapper))
        if (len(past_n_seconds_load_vals) == 1) and (past_n_seconds_load_vals[0] in (1, 3)):
            # Action taken in this round. Hence use "1.5" to avoid immediate action in next round
            cpu_low_high_mapper[mapper_idx] = 2
        elif cpu_use_percentage_average <= client_conf['auto_scaler_threshold_load_low']:
            # Below average load
            cpu_low_high_mapper[mapper_idx] = 1
        elif client_conf['auto_scaler_threshold_load_high'] <= cpu_use_percentage_average:
            # Above average load
            cpu_low_high_mapper[mapper_idx] = 3
        else:
            # Normal load
            cpu_low_high_mapper[mapper_idx] = 2
        mapper_idx = (mapper_idx + 1) % auto_scaler_load_minimum_seconds
    pass


def signal_handler(sig, frame):
    # REFER: https://stackoverflow.com/questions/1112343/how-do-i-capture-sigint-in-python
    print('\n\nYou pressed Ctrl+C ! Exiting...\n')
    sys.exit(0)


if __name__ == '__main__':
    # If no parameters passed
    # print(sys.argv)  # ['auto_scaler.py']

    # If "0" is passed as a command line argument, then
    #     The client will not be informed about already running VM's when the autoscaler runs for the first time
    # Else
    #     The client will be informed as soon as the autoscaler starts

    signal.signal(signal.SIGINT, signal_handler)
    with open('client.conf') as f:
        CLIENT_CONF = json.load(f)

    run_autoscaler(
        client_conf=CLIENT_CONF,
        initially_add_running_servers=False if (len(sys.argv) == 2 and sys.argv[1] == '0') else True
    )

    # # Establish connection with the VM Manager
    # conn = libvirt.open('qemu:///system')
    #
    # # Get List of VM's/Domain's used by my application
    # conn.listDomainsID()  # Only ONLINE domain ID's are returned
    # conn.listAllDomains()  # List of ID of all domains (The ID is present even when the domain is Powered OFF)
    # conn.getAllDomainStats()
    #
    # # Find CPU usage of the VM's
    # a = conn.lookupByID(1)
    # b = conn.lookupByName('ubuntu18.04-000000001')
    # pprint(a.getCPUStats(True))
    #
    # # Create new VM and launch it with "server.py"
    # b.ID()
    # b.UUID()
    # b.UUIDString()
    # pass
