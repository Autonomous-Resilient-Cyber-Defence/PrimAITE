# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from ipaddress import IPv4Address
from typing import Any, Final

from pydantic import BeforeValidator
from typing_extensions import Annotated


# Define a custom type IPV4Address using the typing_extensions.Annotated.
# Annotated is used to attach metadata to type hints. In this case, it's used to associate the ipv4_validator
# with the IPv4Address type, ensuring that any usage of IPV4Address undergoes validation before assignment.
def ipv4_validator(v: Any) -> IPv4Address:
    """
    Validate the input and ensure it can be converted to an IPv4Address instance.

    This function takes an input `v`, and if it's not already an instance of IPv4Address, it tries to convert it to one.
    If the conversion is successful, the IPv4Address instance is returned. This is useful for ensuring that any input
    data is strictly in the format of an IPv4 address.

    :param v: The input value that needs to be validated or converted to IPv4Address.
    :return: An instance of IPv4Address.
    :raises ValueError: If `v` is not a valid IPv4 address and cannot be converted to an instance of IPv4Address.
    """
    if isinstance(v, IPv4Address):
        return v

    return IPv4Address(v)


IPV4Address: Final[Annotated] = Annotated[IPv4Address, BeforeValidator(ipv4_validator)]
"""
IPv4Address with with IPv4Address with with pre-validation and auto-conversion from str using ipv4_validator..

This type is essentially an IPv4Address from the standard library's ipaddress module,
but with added validation logic. If you use this custom type, the ipv4_validator function
will automatically check and convert the input value to an instance of IPv4Address before
any Pydantic model uses it. This ensures that any field marked with this type is not just
an IPv4Address in form, but also valid according to the rules defined in ipv4_validator.
"""

# Define a custom port validator
Port: Final[Annotated] = Annotated[int, BeforeValidator(lambda n: 0 <= n <= 65535)]
"""Validates that network ports lie in the appropriate range of [0,65535]."""

# Define a custom IP protocol validator
PROTOCOL_LOOKUP: dict[str, str] = dict(
    NONE="none",
    TCP="tcp",
    UDP="udp",
    ICMP="icmp",
)
"""
Lookup table used for compatibility with PrimAITE <= 3.3. Configs with the capitalised protocol names are converted
to lowercase at runtime.
"""
VALID_PROTOCOLS = ["none", "tcp", "udp", "icmp"]
"""Supported protocols."""


def protocol_validator(v: Any) -> str:
    """
    Validate that IP Protocols are chosen from the list of supported IP Protocols.

    The protocol list is dynamic because plugins are able to extend it, therefore it is necessary to use this custom
    validator instead of being able to specify a union of string literals.
    """
    if v in PROTOCOL_LOOKUP:
        return PROTOCOL_LOOKUP(v)
    if v in VALID_PROTOCOLS:
        return v
    raise ValueError(f"{v} is not a valid IP Protocol. It must be one of the following: {VALID_PROTOCOLS}")


IPProtocol: Final[Annotated] = Annotated[str, BeforeValidator(protocol_validator)]
"""Validates that IP Protocols used in the simulation belong to the list of supported protocols."""
