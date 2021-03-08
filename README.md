# CS695-Assignment-2

- Programming Assignment 2 - Build your own auto-scaling client server application using the libvirt API
- Problem Statement: [https://www.cse.iitb.ac.in/~cs695/pa/pa2.html](https://www.cse.iitb.ac.in/~cs695/pa/pa2.html)

[comment]: <> (- [Problem Statement]&#40;./Problem%20Statement.pdf&#41;)

[comment]: <> (- [My Solution]&#40;./kvm-hello-world/Answers.md&#41;)

### Standard things use in programming

- All configuration files are stored in JSON format
- Server program configuration is stored in `server.conf`
- Client program configuration is stored in `client.conf`
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

cd /var/lib/libvirt
ls -l images
ls -l /etc/libvirt/libvirt.conf
cp /etc/libvirt/libvirt.conf ~/.config/libvirt/

# ---

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
            * `sudo apt-get install libvirt-dev`
        - https://pypi.org/project/libvirt-python/
            * `pip install libvirt-python`
    - https://unix.stackexchange.com/questions/599651/whats-the-purpose-of-kvm-libvirt-and-libvirt-qemu-groups-in-linux
- **Introduction**
    - https://ubuntu.com/server/docs/virtualization-libvirt
    - https://youtu.be/qr3d-4ctZk4
    - https://youtu.be/HfNKpT2jo7U
- https://libvirt.org/docs.html
- https://libvirt.org/downloads.html
- Programming
    - https://www.machinelearningplus.com/python/python-logging-guide/
    - https://uynguyen.github.io/2018/04/30/Big-Endian-vs-Little-Endian/
    - https://stackoverflow.com/questions/21017698/converting-int-to-bytes-in-python-3
        * https://docs.python.org/2/library/struct.html#struct.pack
    - https://stackoverflow.com/questions/34009653/convert-bytes-to-int
    - https://www.geeksforgeeks.org/python-convert-string-to-bytes/
    - https://tutorialedge.net/python/udp-client-server-python/
        * https://www.geeksforgeeks.org/udp-server-client-implementation-c/
        * https://stackoverflow.com/questions/1593946/what-is-af-inet-and-why-do-i-need-it
    - https://www.studytonight.com/network-programming-in-python/working-with-udp-sockets
    - https://pythontic.com/modules/socket/udp-client-server-example
- https://stackoverflow.com/questions/40468370/what-does-cpu-time-represent-exactly-in-libvirtvirsh net-list
- https://stackoverflow.com/questions/19057915/libvirt-fetch-ipv4-address-from-guest
- https://unix.stackexchange.com/questions/33191/how-to-find-the-ip-address-of-a-kvm-virtual-machine-that-i-can-ssh-into-it
- https://www.cyberciti.biz/faq/find-ip-address-of-linux-kvm-guest-virtual-machine/

