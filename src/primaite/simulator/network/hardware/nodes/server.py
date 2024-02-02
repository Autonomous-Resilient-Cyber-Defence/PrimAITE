from primaite.simulator.network.hardware.nodes.host import Host


class Server(Host):
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
    pass
