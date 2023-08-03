from typing import Any, Optional

from pydantic import BaseModel

from primaite import getLogger
from primaite.simulator.network.transmission.network_layer import ICMPHeader, IPPacket, IPProtocol
from primaite.simulator.network.transmission.primaite_layer import PrimaiteHeader
from primaite.simulator.network.transmission.transport_layer import TCPHeader, UDPHeader

_LOGGER = getLogger(__name__)


class EthernetHeader(BaseModel):
    """
    Represents the Ethernet layer of a network frame.

    :param src_mac_addr: Source MAC address.
    :param dst_mac_addr: Destination MAC address.

    :Example:

    >>> ethernet = EthernetHeader(
    ...     src_mac_addr='AA:BB:CC:DD:EE:FF',
    ...     dst_mac_addr='11:22:33:44:55:66'
    ... )
    """

    src_mac_addr: str
    "Source MAC address."
    dst_mac_addr: str
    "Destination MAC address."


class Frame(BaseModel):
    """
    Represents a complete network frame with all layers.

    :param ethernet: Ethernet layer.
    :param ip: IP layer.
    :param tcp: TCP layer.
    :param payload: Payload data in the frame.

    :Example:

    >>> from ipaddress import IPv4Address
    >>> frame=Frame(
    ...     ethernet=EthernetHeader(
    ...         src_mac_addr='AA:BB:CC:DD:EE:FF',
    ...         dst_mac_addr='11:22:33:44:55:66'
    ...     ),
    ...     ip=IPPacket(
    ...         src_ip=IPv4Address('192.168.0.1'),
    ...         dst_ip=IPv4Address('10.0.0.1'),
    ...     ),
    ...     tcp=TCPHeader(
    ...         src_port=8080,
    ...         dst_port=80,
    ...     ),
    ...     payload=b"Hello, World!"
    ... )
    """

    def __init__(self, **kwargs):
        if kwargs.get("tcp") and kwargs.get("udp"):
            msg = "Network Frame cannot have both a TCP header and a UDP header"
            _LOGGER.error(msg)
            raise ValueError(msg)
        if kwargs["ip"].protocol == IPProtocol.TCP and not kwargs.get("tcp"):
            msg = "Cannot build a Frame using the TCP IP Protocol without a TCPHeader"
            _LOGGER.error(msg)
            raise ValueError(msg)
        if kwargs["ip"].protocol == IPProtocol.UDP and not kwargs.get("UDP"):
            msg = "Cannot build a Frame using the UDP IP Protocol without a UDPHeader"
            _LOGGER.error(msg)
            raise ValueError(msg)
        if kwargs["ip"].protocol == IPProtocol.ICMP and not kwargs.get("icmp"):
            msg = "Cannot build a Frame using the ICMP IP Protocol without a ICMPHeader"
            _LOGGER.error(msg)
            raise ValueError(msg)
        super().__init__(**kwargs)

    ethernet: EthernetHeader
    "Ethernet header."
    ip: IPPacket
    "IP packet."
    tcp: Optional[TCPHeader] = None
    "TCP header."
    udp: Optional[UDPHeader] = None
    "UDP header."
    icmp: Optional[ICMPHeader] = None
    "ICMP header."
    primaite: PrimaiteHeader = PrimaiteHeader()
    "PrimAITE header."
    payload: Optional[Any] = None
    "Raw data payload."

    @property
    def size(self) -> int:
        """The size in Bytes."""
        return len(self.model_dump_json().encode("utf-8"))
