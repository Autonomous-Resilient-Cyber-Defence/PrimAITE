import secrets
from enum import Enum
from ipaddress import IPv4Address
from typing import Union

from pydantic import BaseModel, field_validator, validate_call
from pydantic_core.core_schema import FieldValidationInfo

from primaite import getLogger

_LOGGER = getLogger(__name__)


class IPProtocol(Enum):
    """Enum representing transport layer protocols in IP header."""

    TCP = "tcp"
    UDP = "udp"
    ICMP = "icmp"


class Precedence(Enum):
    """
    Enum representing the Precedence levels in Quality of Service (QoS) for IP packets.

    Precedence values range from 0 to 7, indicating different levels of priority.

    Members:
    - ROUTINE: 0 - Lowest priority level, used for ordinary data traffic that does not require special treatment.
    - PRIORITY: 1 - Higher priority than ROUTINE, used for traffic that needs a bit more importance.
    - IMMEDIATE: 2 - Used for more urgent traffic that requires immediate handling and minimal delay.
    - FLASH: 3 - Used for highly urgent and important traffic that should be processed with high priority.
    - FLASH_OVERRIDE: 4 - Higher priority than FLASH, used for critical traffic that takes precedence over most traffic.
    - CRITICAL: 5 - Reserved for critical commands or control messages that are vital to the operation of the network.
    - INTERNET: 6 - Used for network control messages, such as routing updates, for maintaining network operations.
    - NETWORK: 7 - Highest priority for the most critical network control messages, such as routing protocol hellos.
    """

    ROUTINE = 0
    "Lowest priority level, used for ordinary data traffic that does not require special treatment."
    PRIORITY = 1
    "Higher priority than ROUTINE, used for traffic that needs a bit more importance."
    IMMEDIATE = 2
    "Used for more urgent traffic that requires immediate handling and minimal delay."
    FLASH = 3
    "Used for highly urgent and important traffic that should be processed with high priority."
    FLASH_OVERRIDE = 4
    "Has higher priority than FLASH, used for critical traffic that takes precedence over most other traffic."
    CRITICAL = 5
    "Reserved for critical commands or emergency control messages that are vital to the operation of the network."
    INTERNET = 6
    "Used for network control messages, such as routing updates, essential for maintaining network operations."
    NETWORK = 7
    "Highest priority level, used for the most critical network control messages, such as routing protocol hellos."


class IPPacket(BaseModel):
    """
    Represents the IP layer of a network frame.

    :param src_ip_address: Source IP address.
    :param dst_ip_address: Destination IP address.
    :param protocol: The IP protocol (default is TCP).
    :param ttl: Time to Live (TTL) for the packet.
    :param precedence: Precedence level for Quality of Service (QoS).

    :Example:

    >>> from ipaddress import IPv4Address
    >>> ip_packet = IPPacket(
    ...     src_ip_address=IPv4Address('192.168.0.1'),
    ...     dst_ip_address=IPv4Address('10.0.0.1'),
    ...     protocol=IPProtocol.TCP,
    ...     ttl=64,
    ...     precedence=Precedence.CRITICAL
    ... )
    """

    src_ip_address: IPv4Address
    "Source IP address."
    dst_ip_address: IPv4Address
    "Destination IP address."
    protocol: IPProtocol = IPProtocol.TCP
    "IPProtocol."
    ttl: int = 64
    "Time to Live (TTL) for the packet."
    precedence: Precedence = Precedence.ROUTINE
    "Precedence level for Quality of Service (default is Precedence.ROUTINE)."

    def __init__(self, **kwargs):
        if not isinstance(kwargs["src_ip_address"], IPv4Address):
            kwargs["src_ip_address"] = IPv4Address(kwargs["src_ip_address"])
        if not isinstance(kwargs["dst_ip_address"], IPv4Address):
            kwargs["dst_ip_address"] = IPv4Address(kwargs["dst_ip_address"])
        super().__init__(**kwargs)
