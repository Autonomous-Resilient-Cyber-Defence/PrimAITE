# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
import secrets
from enum import Enum
from typing import Union

from pydantic import BaseModel, field_validator, validate_call
from pydantic_core.core_schema import ValidationInfo

from primaite import getLogger

_LOGGER = getLogger(__name__)


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
    ROUTER_ADVERTISEMENT = 9
    "Router Advertisement."
    ROUTER_SOLICITATION = 10
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
    def _icmp_type_must_have_icmp_code(cls, v: int, info: ValidationInfo) -> int:
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
