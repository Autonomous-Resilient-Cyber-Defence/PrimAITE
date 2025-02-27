# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
# Define a custom port validator
from typing import Any

from pydantic import BeforeValidator, TypeAdapter, ValidationError
from typing_extensions import Annotated, Final

PORT_LOOKUP: dict[str, int] = dict(
    UNUSED=-1,
    NONE=0,
    WOL=9,
    FTP_DATA=20,
    FTP=21,
    SSH=22,
    SMTP=25,
    DNS=53,
    HTTP=80,
    POP3=110,
    SFTP=115,
    NTP=123,
    IMAP=143,
    SNMP=161,
    SNMP_TRAP=162,
    ARP=219,
    LDAP=389,
    HTTPS=443,
    SMB=445,
    IPP=631,
    SQL_SERVER=1433,
    MYSQL=3306,
    RDP=3389,
    RTP=5004,
    RTP_ALT=5005,
    DNS_ALT=5353,
    HTTP_ALT=8080,
    HTTPS_ALT=8443,
    POSTGRES_SERVER=5432,
)
"""
Lookup table used for compatibility with PrimAITE <= 3.3. Configs with named ports names are converted
to port integers at runtime.
"""


def port_validator(v: Any) -> int:
    """
    Validate that Ports are chosen from the list of supported Ports.

    The protocol list is dynamic because plugins are able to extend it, therefore it is necessary to use this custom
    validator instead of being able to specify a union of string literals.
    """
    if isinstance(v, str) and v in PORT_LOOKUP:
        v = PORT_LOOKUP[v]
    if isinstance(v, int) and (0 <= v <= 65535):
        return v
    raise ValueError(f"{v} is not a valid Port. It must be an integer in the range [0,65535] or ")


Port: Final[Annotated] = Annotated[int, BeforeValidator(port_validator)]
"""Validates that network ports lie in the appropriate range of [0,65535]."""
_PortTypeAdapter = TypeAdapter(Port)


def is_valid_port(v: Any) -> bool:
    """Convenience method to return true if the value matches the schema, and false otherwise."""
    try:
        _PortTypeAdapter.validate_python(v)
        return True
    except ValidationError:
        return False
