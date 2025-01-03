# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
# Define a custom IP protocol validator
from typing import Any

from pydantic import BeforeValidator, TypeAdapter, ValidationError
from typing_extensions import Annotated, Final

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
    if isinstance(v, str) and v in PROTOCOL_LOOKUP:
        return PROTOCOL_LOOKUP[v]
    if v in VALID_PROTOCOLS:
        return v
    raise ValueError(f"{v} is not a valid IP Protocol. It must be one of the following: {VALID_PROTOCOLS}")


IPProtocol: Final[Annotated] = Annotated[str, BeforeValidator(protocol_validator)]
"""Validates that IP Protocols used in the simulation belong to the list of supported protocols."""
_IPProtocolTypeAdapter = TypeAdapter(IPProtocol)


def is_valid_protocol(v: Any) -> bool:
    """Convenience method to return true if the value matches the schema, and false otherwise."""
    try:
        _IPProtocolTypeAdapter.validate_python(v)
        return True
    except ValidationError:
        return False
