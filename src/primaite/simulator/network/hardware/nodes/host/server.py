# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

from pydantic import Field

from primaite.simulator.network.hardware.nodes.host.host_node import HostNode


class Server(HostNode, identifier="server"):
    """
    A basic Server class.

    Example:
        >>> server_a = Server(
            hostname="server_a",
            ip_address="192.168.1.10",
            subnet_mask="255.255.255.0",
            default_gateway="192.168.1.1"
        )
        >>> server_a.power_on()

    Instances of Server come 'pre-packaged' with the following:

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

    class ConfigSchema(HostNode.ConfigSchema):
        """Configuration Schema for Server class."""

        hostname: str = "server"

    config: ConfigSchema = Field(default_factory=lambda: Server.ConfigSchema())


class Printer(HostNode, identifier="printer"):
    """Printer? I don't even know her!."""

    # TODO: Implement printer-specific behaviour

    class ConfigSchema(HostNode.ConfigSchema):
        """Configuration Schema for Printer class."""

        hostname: str = "printer"

    config: ConfigSchema = Field(default_factory=lambda: Printer.ConfigSchema())
