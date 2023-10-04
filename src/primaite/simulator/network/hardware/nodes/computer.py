from primaite.simulator.network.hardware.base import NIC, Node
from primaite.simulator.system.services.dns.dns_client import DNSClient
from primaite.simulator.system.services.ftp.ftp_client import FTPClient


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
        self._install_system_software()

    def _install_system_software(self):
        """Install System Software - software that is usually provided with the OS."""
        # DNS Client
        self.software_manager.install(DNSClient)

        # FTP
        self.software_manager.install(FTPClient)

        super()._install_system_software()
