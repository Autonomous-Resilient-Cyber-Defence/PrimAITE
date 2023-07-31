from __future__ import annotations

import re
import secrets
from ipaddress import IPv4Address, IPv4Network
from typing import Any, Dict, List, Optional, Union

from primaite import getLogger
from primaite.exceptions import NetworkError
from primaite.simulator.core import SimComponent

_LOGGER = getLogger(__name__)


def generate_mac_address(oui: Optional[str] = None) -> str:
    """
    Generate a random MAC Address.

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
            msg = f"Invalid oui. The oui should be in the format xx:xx:xx, where x is a hexadecimal digit, got '{oui}'"
            raise ValueError(msg)
        oui_bytes = [int(chunk, 16) for chunk in oui.split(":")]
        mac = oui_bytes + random_bytes[len(oui_bytes) :]
    else:
        mac = random_bytes

    return ":".join(f"{b:02x}" for b in mac)


class NIC(SimComponent):
    """
    Models a Network Interface Card (NIC) in a computer or network device.

    :param ip_address: The IPv4 address assigned to the NIC.
    :param subnet_mask: The subnet mask assigned to the NIC.
    :param gateway: The default gateway IP address for forwarding network traffic to other networks.
    :param mac_address: The MAC address of the NIC. Defaults to a randomly set MAC address.
    :param speed: The speed of the NIC in Mbps (default is 100 Mbps).
    :param mtu: The Maximum Transmission Unit (MTU) of the NIC in Bytes, representing the largest data packet size it
        can handle without fragmentation (default is 1500 B).
    :param wake_on_lan: Indicates if the NIC supports Wake-on-LAN functionality.
    :param dns_servers: List of IP addresses of DNS servers used for name resolution.
    """

    ip_address: Union[str, IPv4Address]
    "The IP address assigned to the NIC for communication on an IP-based network."
    subnet_mask: str
    "The subnet mask assigned to the NIC."
    gateway: Union[str, IPv4Address]
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

    def model_post_init(self, __context: Any) -> None:
        """
        Post init function converts string IPs to IPv$Address and checks for proper IP address and gateway config.

        :raises ValueError: When the ip_address and gateway are the same. And when the ip_address/subnet mask are a
        network address.
        """
        if not isinstance(self.ip_address, IPv4Address):
            self.ip_address: IPv4Address = IPv4Address(self.ip_address)
        if not isinstance(self.gateway, IPv4Address):
            self.gateway: IPv4Address = IPv4Address(self.gateway)
        if self.ip_address == self.gateway:
            msg = f"NIC ip address {self.ip_address} cannot be the same as the gateway {self.gateway}"
            _LOGGER.error(msg)
            raise ValueError(msg)
        if self.ip_network.network_address == self.ip_address:
            msg = (
                f"Failed to set IP address {self.ip_address} and subnet mask {self.subnet_mask} as it is a "
                f"network address {self.ip_network.network_address}"
            )
            _LOGGER.error(msg)
            raise ValueError(msg)

    @property
    def ip_network(self) -> IPv4Network:
        """
        Return the IPv4Network of the NIC.

        :return: The IPv4Network from the ip_address/subnet mask.
        """
        return IPv4Network(f"{self.ip_address}/{self.subnet_mask}", strict=False)

    def connect_link(self, link: Link):
        """
        Connect the NIC to a link.

        :param link: The link to which the NIC is connected.
        :type link: :class:`~primaite.simulator.network.physical_layer.Link`
        :raise NetworkError: When an attempt to connect a Link is made while the NIC has a connected Link.
        """
        if not self.connected_link:
            if self.connected_link != link:
                # TODO: Inform the Node that a link has been connected
                self.connected_link = link
            else:
                _LOGGER.warning(f"Cannot connect link to NIC ({self.mac_address}) as it is already connected")
        else:
            msg = f"Cannot connect link to NIC ({self.mac_address}) as it already has a connection"
            _LOGGER.error(msg)
            raise NetworkError(msg)

    def disconnect_link(self):
        """Disconnect the NIC from the connected :class:`~primaite.simulator.network.physical_layer.Link`."""
        if self.connected_link.endpoint_a == self:
            self.connected_link.endpoint_a = None
        if self.connected_link.endpoint_b == self:
            self.connected_link.endpoint_b = None
        self.connected_link = None

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
    "The first NIC connected to the Link."
    endpoint_b: NIC
    "The second NIC connected to the Link."
    bandwidth: int = 100
    "The bandwidth of the Link in Mbps (default is 100 Mbps)."
    current_load: int = 0
    "The current load on the link in Mbps."

    def model_post_init(self, __context: Any) -> None:
        """
        Ensure that endpoint_a and endpoint_b are not the same :class:`~primaite.simulator.network.physical_layer.NIC`.

        :raises ValueError: If endpoint_a and endpoint_b are the same NIC.
        """
        if self.endpoint_a == self.endpoint_b:
            msg = "endpoint_a and endpoint_b cannot be the same NIC"
            _LOGGER.error(msg)
            raise ValueError(msg)
        self.endpoint_a.connect_link(self)
        self.endpoint_b.connect_link(self)

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
