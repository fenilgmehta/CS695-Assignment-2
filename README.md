# CS695-Assignment-2

- Programming Assignment 2 - Build your own auto-scaling client server application using the libvirt API
- [Problem Statement PDF](./Problem%20Statement%20-%20Programming%20Assignment%202.pdf) ([https://www.cse.iitb.ac.in/~cs695/pa/pa2.html](https://www.cse.iitb.ac.in/~cs695/pa/pa2.html))
- [Demo Video](CS695-Assignment-2%20-%20Demo%201%20-%202021-03-10%2022-09-47.mp4)

### Solution Details and Results

- Features:
    - Real time CPU utilization graph
    - Increase the number of server VM's in case of overload
    - Decrease the number of server VM's in case of low load
    - Inform the client program (which plays the role of load balancer) in case of VM failures

- CPU utilization graph plotted in real time by the autoscaler
    - The part to the right of `0` on the x-axis is the deciding factor for the action taken by the autoscaler 

  ![Working of autoscaler program](./CPU%20Usage%20Graph%20of%20VMs.png)

- To run/test the program
    1. Create a VM in Virtual Machine Manager and put the `server.py` code in it.
    2. Configure the VM to autostart the `server.py` program as soon as the OS boots.
    3. Create multiple clones of the same VM and follow a proper naming convention. The numbering should start from 0
        - Example: `AnyPrefix-0000`, `AnyPrefix-0001`, `AnyPrefix-0002`
        - Write about this naming convention inside the `client.conf` file
    4. Launch the first VM - `AnyPrefix-0000`
    5. Open terminal and run `client.py`, `client_communicator.py`, `auto_scaler.py`
    6. Use `client_communicator.py` to configure the `client.py` at runtime. Supported functionalities:
        - Add server syntax    = `+ <IP_ADDRESS> <PORT>`
            - Here, IP Address and Port Number are of the server program.
        - Remove server syntax = `- <IP_ADDRESS> <PORT>`
            - Here, IP Address and Port Number are of the server program.
        - Remove all servers   = `clear_servers`
        - Refresh the servers list = `refresh`
            - libvirt API is used for checking the list of online VM's and those VM's whose name prefix does not match with the one mentioned in the `client.conf` are removed from the list.
        - Change client's request/query generation speed:
            - `low`
            - `mid`
            - `high`
            - `custom 0.3`   <--- here, 0.3 can be replaced with any floating point value
    7. View the realtime graph plotted by the `auto_scaler.py` to get an insight into the working of the autoscaler


### Standard things use in programming

- All configuration files are stored in JSON format
- `server.py` configuration is stored in `server.conf`
- `client.py` configuration is stored in `client.conf`
    - This same file is used by `auto_scaler.py` as well because, the `client.py` in this assignment is equivalent to a
      load balancer in real life
    - `client_communicator.py` also uses the same configuration file
- The client-server communication message configuration is stored in `message.conf`
- `big-endian` format in used for numbers when converted to bytes
- `4 bytes - unsigned int` is used to represent client request integers
- `8 bytes - unsigned long long` is used to represent server response integers


### Useful Commands

```sh
# virsh is the main interface for managing virsh guest domains.
virsh -V
virsh -c qemu:///system list   # connect locally as root to the daemon supervising QEMU and KVM domains
virsh -c qemu:///session list  # connect locally as a normal user to his own set of QEMU and KVM domains

# ---

# libvirt internals
cd /var/lib/libvirt
ls -l images
ls -l /etc/libvirt/libvirt.conf
cp /etc/libvirt/libvirt.conf ~/.config/libvirt/

# ---

# Network commands
virsh dumpxml ubuntu18.04
virsh net-list
virsh net-dhcp-leases default
virsh domifaddr ubuntu18.04-1
route

```


### References

- **Installation**
    - https://help.ubuntu.com/community/KVM/Installation
      ```sh
      # Commands used on Linux Mint 20
      sudo apt-get install qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virt-manager
      sudo adduser `id -un` libvirt  # sudo adduser $USER libvirt  # sudo usermod -aG libvirt $USERNAME
      sudo adduser `id -un` kvm      # sudo adduser $USER kvm      # sudo usermod -aG kvm $USERNAME

      # Probably reboot/restart needed

      # Check the installation
      virsh -c qemu:///system list
      sudo ls -la /var/run/libvirt/libvirt-sock
      ls -l /dev/kvm
      service libvirtd status
      ```
    - To install libvirt python library in virtual environment/conda
        - https://stackoverflow.com/questions/45473463/pip-install-libvirt-python-fails-in-virtualenv
            - `sudo apt-get install libvirt-dev`
        - https://pypi.org/project/libvirt-python/
            - `pip install libvirt-python`
    - https://unix.stackexchange.com/questions/599651/whats-the-purpose-of-kvm-libvirt-and-libvirt-qemu-groups-in-linux
- **Introduction**
    - https://ubuntu.com/server/docs/virtualization-libvirt
    - https://youtu.be/qr3d-4ctZk4
    - https://youtu.be/HfNKpT2jo7U
    - https://youtu.be/6435eNKpyYw
- **libvirt**
    - https://libvirt.org/docs.html
    - https://libvirt.org/downloads.html
    - https://libvirt.org/html/index.html (Good)
    - https://libvirt.org/html/libvirt-libvirt-domain.html (Good)
- **Client Server Programming**
    - https://uynguyen.github.io/2018/04/30/Big-Endian-vs-Little-Endian/
    - https://stackoverflow.com/questions/21017698/converting-int-to-bytes-in-python-3
        - https://docs.python.org/2/library/struct.html#struct.pack
    - https://stackoverflow.com/questions/34009653/convert-bytes-to-int
    - https://www.geeksforgeeks.org/python-convert-string-to-bytes/
    - https://tutorialedge.net/python/udp-client-server-python/
        - https://www.geeksforgeeks.org/udp-server-client-implementation-c/
        - https://stackoverflow.com/questions/1593946/what-is-af-inet-and-why-do-i-need-it
    - https://www.studytonight.com/network-programming-in-python/working-with-udp-sockets
    - https://pythontic.com/modules/socket/udp-client-server-example
- **Other references**
    - https://www.machinelearningplus.com/python/python-logging-guide/
    - https://stackoverflow.com/questions/40468370/what-does-cpu-time-represent-exactly-in-libvirtvirsh
    - https://stackoverflow.com/questions/19057915/libvirt-fetch-ipv4-address-from-guest
    - https://unix.stackexchange.com/questions/33191/how-to-find-the-ip-address-of-a-kvm-virtual-machine-that-i-can-ssh-into-it
    - https://www.cyberciti.biz/faq/find-ip-address-of-linux-kvm-guest-virtual-machine/

