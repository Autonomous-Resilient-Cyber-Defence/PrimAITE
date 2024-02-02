from primaite.simulator.network.hardware.base import NIC, Node
from primaite.simulator.system.applications.web_browser import WebBrowser
from primaite.simulator.system.services.arp.host_arp import HostARP
from primaite.simulator.system.services.dns.dns_client import DNSClient
from primaite.simulator.system.services.ftp.ftp_client import FTPClient
from primaite.simulator.system.services.icmp.icmp import ICMP
from primaite.simulator.system.services.ntp.ntp_client import NTPClient


class Host(Node):
    """
    A basic Host class.

    Example:
        >>> pc_a = Host(
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
        # ARP Service
        self.software_manager.install(HostARP)

        # ICMP Service
        self.software_manager.install(ICMP)

        # DNS Client
        self.software_manager.install(DNSClient)

        # FTP Client
        self.software_manager.install(FTPClient)

        # NTP Client
        self.software_manager.install(NTPClient)

        # Web Browser
        self.software_manager.install(WebBrowser)

        super()._install_system_software()
