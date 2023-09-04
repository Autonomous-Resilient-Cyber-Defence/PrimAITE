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


class ICMPType(Enum):
    """Enumeration of common ICMP (Internet Control Message Protocol) types."""

    ECHO_REPLY = 0
    "Echo Reply message."
    DESTINATION_UNREACHABLE = 3
    "Destination Unreachable."
    REDIRECT = 5
    "Redirect."
    ECHO_REQUEST = 8
    "Echo Request (ping)."
    ROUTER_ADVERTISEMENT = 10
    "Router Advertisement."
    ROUTER_SOLICITATION = 11
    "Router discovery/selection/solicitation."
    TIME_EXCEEDED = 11
    "Time Exceeded."
    TIMESTAMP_REQUEST = 13
    "Timestamp Request."
    TIMESTAMP_REPLY = 14
    "Timestamp Reply."


@validate_call
def get_icmp_type_code_description(icmp_type: ICMPType, icmp_code: int) -> Union[str, None]:
    """
    Maps ICMPType and code pairings to their respective description.

    :param icmp_type: An ICMPType.
    :param icmp_code: An icmp code.
    :return: The icmp type and code pairing description if it exists, otherwise returns None.
    """
    icmp_code_descriptions = {
        ICMPType.ECHO_REPLY: {0: "Echo reply"},
        ICMPType.DESTINATION_UNREACHABLE: {
            0: "Destination network unreachable",
            1: "Destination host unreachable",
            2: "Destination protocol unreachable",
            3: "Destination port unreachable",
            4: "Fragmentation required",
            5: "Source route failed",
            6: "Destination network unknown",
            7: "Destination host unknown",
            8: "Source host isolated",
            9: "Network administratively prohibited",
            10: "Host administratively prohibited",
            11: "Network unreachable for ToS",
            12: "Host unreachable for ToS",
            13: "Communication administratively prohibited",
            14: "Host Precedence Violation",
            15: "Precedence cutoff in effect",
        },
        ICMPType.REDIRECT: {
            0: "Redirect Datagram for the Network",
            1: "Redirect Datagram for the Host",
        },
        ICMPType.ECHO_REQUEST: {0: "Echo request"},
        ICMPType.ROUTER_ADVERTISEMENT: {0: "Router Advertisement"},
        ICMPType.ROUTER_SOLICITATION: {0: "Router discovery/selection/solicitation"},
        ICMPType.TIME_EXCEEDED: {0: "TTL expired in transit", 1: "Fragment reassembly time exceeded"},
        ICMPType.TIMESTAMP_REQUEST: {0: "Timestamp Request"},
        ICMPType.TIMESTAMP_REPLY: {0: "Timestamp reply"},
    }
    return icmp_code_descriptions[icmp_type].get(icmp_code)


class ICMPPacket(BaseModel):
    """Models an ICMP Packet."""

    icmp_type: ICMPType = ICMPType.ECHO_REQUEST
    "ICMP Type."
    icmp_code: int = 0
    "ICMP Code."
    identifier: int
    "ICMP identifier (16 bits randomly generated)."
    sequence: int = 0
    "ICMP message sequence number."

    def __init__(self, **kwargs):
        if not kwargs.get("identifier"):
            kwargs["identifier"] = secrets.randbits(16)
        super().__init__(**kwargs)

    @field_validator("icmp_code")  # noqa
    @classmethod
    def _icmp_type_must_have_icmp_code(cls, v: int, info: FieldValidationInfo) -> int:
        """Validates the icmp_type and icmp_code."""
        icmp_type = info.data["icmp_type"]
        if get_icmp_type_code_description(icmp_type, v):
            return v
        msg = f"No Matching ICMP code for type:{icmp_type.name}, code:{v}"
        _LOGGER.error(msg)
        raise ValueError(msg)

    def code_description(self) -> str:
        """The icmp_code description."""
        description = get_icmp_type_code_description(self.icmp_type, self.icmp_code)
        if description:
            return description
        msg = f"No Matching ICMP code for type:{self.icmp_type.name}, code:{self.icmp_code}"
        _LOGGER.error(msg)
        raise ValueError(msg)


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
