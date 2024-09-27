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
