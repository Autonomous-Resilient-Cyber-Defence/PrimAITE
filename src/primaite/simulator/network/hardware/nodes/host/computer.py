from primaite.simulator.network.hardware.nodes.host.host_node import HostNode


class Computer(HostNode):
    """
    A basic Computer class.

    Example:
        >>> pc_a = Computer(
            hostname="pc_a",
            ip_address="192.168.1.10",
            subnet_mask="255.255.255.0",
            default_gateway="192.168.1.1"
        )
        >>> pc_a.power_on()

    Instances of computer come 'pre-packaged' with the following:

    * Core Functionality:
        * Packet Capture
        * Sys Log
    * Services:
        * ARP Service
        * ICMP Service
        * DNS Client
        * FTP Client
        * NTP Client
    * Applications:
        * Web Browser
    """

    pass
