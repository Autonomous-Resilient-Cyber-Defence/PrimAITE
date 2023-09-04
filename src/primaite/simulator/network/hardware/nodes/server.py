from primaite.simulator.network.hardware.nodes.computer import Computer


class Server(Computer):
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
