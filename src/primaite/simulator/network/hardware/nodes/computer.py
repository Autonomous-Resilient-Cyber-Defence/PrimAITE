from ipaddress import IPv4Address

from primaite.simulator.network.hardware.base import Node, NIC


class Computer(Node):
    """
    A basic computer class.

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
      * ARP.
      * ICMP.
      * Packet Capture.
      * Sys Log.
    * Services:
      * DNS Client.
      * FTP Client.
      * LDAP Client.
      * NTP Client.
    * Applications:
      * Email Client.
      * Web Browser.
    * Processes:
        * Placeholder.
    """

    def __init__(self, **kwargs):
        for key in {"ip_address", "subnet_mask", "default_gateway"}:
            if key in kwargs:
                if not isinstance(kwargs[key], IPv4Address):
                    kwargs[key] = IPv4Address(kwargs[key])
        super().__init__(**kwargs)
        self.connect_nic(NIC(ip_address=kwargs["ip_address"], subnet_mask=kwargs["subnet_mask"]))
