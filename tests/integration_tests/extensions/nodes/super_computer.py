# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from typing import ClassVar, Dict

from primaite.simulator.network.hardware.nodes.host.host_node import HostNode, NIC
from primaite.simulator.system.services.ftp.ftp_client import FTPClient
from primaite.utils.validation.ipv4_address import IPV4Address


class SuperComputer(HostNode, identifier="supercomputer"):
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

    SYSTEM_SOFTWARE: ClassVar[Dict] = {**HostNode.SYSTEM_SOFTWARE, "FTPClient": FTPClient}

    def __init__(self, ip_address: IPV4Address, subnet_mask: IPV4Address, **kwargs):
        print("--- Extended Component: SuperComputer ---")
        super().__init__(ip_address=ip_address, subnet_mask=subnet_mask, **kwargs)

    pass
