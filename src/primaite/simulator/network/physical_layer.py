from __future__ import annotations

import re
import secrets
from ipaddress import IPv4Address
from typing import Dict, List, Optional

from primaite.simulator.core import SimComponent


def generate_mac_address(oui: Optional[str] = None) -> str:
    """
    Generate a random MAC Address..

    :Example:

    >>> generate_mac_address()
    'ef:7e:97:c8:a8:ce'

    >>> generate_mac_address(oui='aa:bb:cc')
    'aa:bb:cc:42:ba:41'

    :param oui: The Organizationally Unique Identifier (OUI) portion of the MAC address. It should be a string with
        the first 3 bytes (24 bits) in the format "XX:XX:XX".
    :raises ValueError: If the 'oui' is not in the correct format (hexadecimal and 6 characters).
    """
    random_bytes = [secrets.randbits(8) for _ in range(6)]

    if oui:
        oui_pattern = re.compile(r"^([0-9A-Fa-f]{2}[:-]){2}[0-9A-Fa-f]{2}$")
        if not oui_pattern.match(oui):
            raise ValueError(
                f"Invalid oui. The oui should be in the format 'xx:xx:xx', where x is a hexadecimal digit, got '{oui}'."
            )
        oui_bytes = [int(chunk, 16) for chunk in oui.split(":")]
        mac = oui_bytes + random_bytes[len(oui_bytes) :]
    else:
        mac = random_bytes

    return ":".join(f"{b:02x}" for b in mac)


class Link(SimComponent):
    """
    Represents a network link between two network interface cards (NICs).

    :param endpoint_a: The first NIC connected to the Link.
    :type endpoint_a: NIC
    :param endpoint_b: The second NIC connected to the Link.
    :type endpoint_b: NIC
    :param bandwidth: The bandwidth of the Link in Mbps (default is 100 Mbps).
    :type bandwidth: int
    """

    endpoint_a: NIC
    endpoint_b: NIC
    bandwidth: int
    current_load: int = 0

    def __init__(self, endpoint_a: NIC, endpoint_b: NIC, bandwidth: int = 100):
        """
        Initialize the Link instance.

        When a Link is created, it automatically connects the endpoints to itself.

        :param endpoint_a: The first NIC connected to the link.
        :type endpoint_a: NIC
        :param endpoint_b: The second NIC connected to the link.
        :type endpoint_b: NIC
        :param bandwidth: The bandwidth of the link in Mbps (default is 100 Mbps).
        :type bandwidth: int
        :raise ValueError: If endpoint_a equals endpoint_b.
        """
        super().__init__(endpoint_a=endpoint_a, endpoint_b=endpoint_b, bandwidth=bandwidth)
        if self.endpoint_a == self.endpoint_b:
            raise ValueError("endpoint_a and endpoint_b cannot be the same NIC")

    def send_frame(self, sender_nic: NIC, frame):
        """
        Send a network frame from one NIC to another connected NIC.

        :param sender_nic: The NIC sending the frame.
        :type sender_nic: NIC
        :param frame: The network frame to be sent.
        :type frame: Frame
        """
        pass

    def receive_frame(self, sender_nic: NIC, frame):
        """
        Receive a network frame from a connected NIC.

        :param sender_nic: The NIC sending the frame.
        :type sender_nic: NIC
        :param frame: The network frame being received.
        :type frame: Frame
        """
        pass

    def describe_state(self) -> Dict:
        """
        Get the current state of the Libk as a dict.

        :return: A dict containing the current state of the Link.
        """
        pass

    def apply_action(self, action: str):
        """
        Apply an action to the Link.

        :param action: The action to be applied.
        :type action: str
        """
        pass


class NIC(SimComponent):
    """
    Models a Network Interface Card (NIC) in a computer or network device.

    :param ip_address: The IPv4 address assigned to the NIC.
    :param subnet_mask: The subnet mask assigned to the NIC.
    :param gateway: The default gateway IP address for forwarding network traffic to other networks.
    :param mac_address: The MAC address of the NIC. Defaults to a randomly set MAC address.
    :param speed: The speed of the NIC in Mbps.
    :param mtu: The Maximum Transmission Unit (MTU) of the NIC in Bytes, representing the largest data packet size it
        can handle without fragmentation.
    :param wake_on_lan: Indicates if the NIC supports Wake-on-LAN functionality.
    :param dns_servers: List of IP addresses of DNS servers used for name resolution.
    :param connected_link: The link to which the NIC is connected (default is None).
    :param enabled: Indicates whether the NIC is enabled.
    """

    ip_address: IPv4Address
    "The IP address assigned to the NIC for communication on an IP-based network."
    subnet_mask: str
    "The subnet mask assigned to the NIC."
    gateway: IPv4Address
    "The default gateway IP address for forwarding network traffic to other networks. Randomly generated upon creation."
    mac_address: str = generate_mac_address()
    "The MAC address of the NIC. Defaults to a randomly set MAC address."
    speed: Optional[int] = 100
    "The speed of the NIC in Mbps. Default is 100 Mbps."
    mtu: Optional[int] = 1500
    "The Maximum Transmission Unit (MTU) of the NIC in Bytes. Default is 1500 B"
    wake_on_lan: Optional[bool] = False
    "Indicates if the NIC supports Wake-on-LAN functionality."
    dns_servers: List[IPv4Address] = []
    "List of IP addresses of DNS servers used for name resolution."
    connected_link: Optional[Link] = None
    "The Link to which the NIC is connected."
    enabled: bool = False
    "Indicates whether the NIC is enabled."

    def connect_link(self, link: Link):
        """
        Connect the NIC to a link.

        :param link: The link to which the NIC is connected.
        :type link: :class:`~primaite.simulator.network.physical_layer.Link`
        """
        pass

    def disconnect_link(self):
        """Disconnect the NIC from the connected :class:`~primaite.simulator.network.physical_layer.Link`."""
        pass

    def add_dns_server(self, ip_address: IPv4Address):
        """
        Add a DNS server IP address.

        :param ip_address: The IP address of the DNS server to be added.
        :type ip_address: ipaddress.IPv4Address
        """
        pass

    def remove_dns_server(self, ip_address: IPv4Address):
        """
        Remove a DNS server IP Address.

        :param ip_address: The IP address of the DNS server to be removed.
        :type ip_address: ipaddress.IPv4Address
        """
        pass

    def send_frame(self, frame):
        """
        Send a network frame from the NIC to the connected link.

        :param frame: The network frame to be sent.
        :type frame: :class:`~primaite.simulator.network.osi_layers.Frame`
        """
        pass

    def receive_frame(self, frame):
        """
        Receive a network frame from the connected link.

        The Frame is passed to the Node.

        :param frame: The network frame being received.
        :type frame: :class:`~primaite.simulator.network.osi_layers.Frame`
        """
        pass

    def describe_state(self) -> Dict:
        """
        Get the current state of the NIC as a dict.

        :return: A dict containing the current state of the NIC.
        """
        pass

    def apply_action(self, action: str):
        """
        Apply an action to the NIC.

        :param action: The action to be applied.
        :type action: str
        """
        pass
