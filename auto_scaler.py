import libvirt
from pprint import pprint
import time


def get_cpu_usage(domain_obj: libvirt.virDomain, sleep_time: int = 1) -> float:
    """
    REFER: https://stackoverflow.com/questions/40468370/what-does-cpu-time-represent-exactly-in-libvirt
    :param domain_obj:
    :param sleep_time: The difference in time interval in seconds after
                       which the second time CPU stats are to be fetched
    :return: Percentage of CPU usage
    """
    # The time values returned by "getCPUStats" is in nanoseconds
    cpu_stat_1 = domain_obj.getCPUStats(True)[0]
    time.sleep(sleep_time)
    cpu_stat_2 = domain_obj.getCPUStats(True)[0]
    cpu_percent = 100 * ((cpu_stat_2['cpu_time'] - cpu_stat_1['cpu_time']) / 1000000000) / sleep_time
    domain_cpu_cores = len(domain_obj.vcpus()[0])
    return cpu_percent / domain_cpu_cores


def get_ip_address(domain_object: libvirt.virDomain):
    """:return: IPv4 address of the domain_object"""
    dom_connect: libvirt.virConnect = domain_object.connect()
    dom_networks: libvirt.virNetwork = dom_connect.listAllNetworks()
    return dom_networks[0].DHCPLeases()[0]['ipaddr']


def get_ip_address_log(network_name: str = 'default'):
    # REFER: https://stackoverflow.com/questions/19057915/libvirt-fetch-ipv4-address-from-guest
    for lease in conn.networkLookupByName(network_name).DHCPLeases():
        print(lease)


# Establish connection with the VM Manager
conn = libvirt.open('qemu:///system')

# Get List of VM's/Domain's used by my application
conn.listDomainsID()  # Only ONLINE domain ID's are returned
conn.listAllDomains()  # List of ID of all domains (The ID is present even when the domain is Powered OFF)
conn.getAllDomainStats()

# Find CPU usage of the VM's
a = conn.lookupByID(1)
b = conn.lookupByName('ubuntu18.04')
pprint(a.getCPUStats(True))

# Create new VM and launch it with "server.py"
b.ID()
b.UUID()
b.UUIDString()
print(b.XMLDesc())
