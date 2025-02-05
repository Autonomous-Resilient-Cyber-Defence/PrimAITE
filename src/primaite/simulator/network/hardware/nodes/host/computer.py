# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from typing import ClassVar, Dict

from pydantic import Field

from primaite.simulator.network.hardware.nodes.host.host_node import HostNode
from primaite.simulator.system.services.ftp.ftp_client import FTPClient


class Computer(HostNode, discriminator="computer"):
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

    SYSTEM_SOFTWARE: ClassVar[Dict] = {**HostNode.SYSTEM_SOFTWARE, "ftp-client": FTPClient}

    class ConfigSchema(HostNode.ConfigSchema):
        """Configuration Schema for Computer class."""

        hostname: str = "Computer"

    config: ConfigSchema = Field(default_factory=lambda: Computer.ConfigSchema())

    pass
