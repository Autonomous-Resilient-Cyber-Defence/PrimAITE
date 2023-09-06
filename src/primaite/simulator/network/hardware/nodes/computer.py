from primaite.simulator.network.hardware.base import NIC, Node


class Computer(Node):
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
        * ARP
        * ICMP
        * Packet Capture
        * Sys Log
    * Services:
        * DNS Client
        * FTP Client
        * LDAP Client
        * NTP Client
    * Applications:
        * Email Client
        * Web Browser
    * Processes:
        * Placeholder
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect_nic(NIC(ip_address=kwargs["ip_address"], subnet_mask=kwargs["subnet_mask"]))
