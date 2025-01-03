# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
import pytest

from primaite.utils.validation.ip_protocol import IPProtocol, is_valid_protocol, PROTOCOL_LOOKUP, protocol_validator


def test_port_conversion():
    for proto_name, proto_val in PROTOCOL_LOOKUP.items():
        assert protocol_validator(proto_name) == proto_val
        assert is_valid_protocol(proto_name)


def test_port_passthrough():
    for proto_val in PROTOCOL_LOOKUP.values():
        assert protocol_validator(proto_val) == proto_val
        assert is_valid_protocol(proto_val)


def test_invalid_ports():
    for port in (123, "abcdefg", "NONEXISTENT_PROTO"):
        with pytest.raises(ValueError):
            protocol_validator(port)
        assert not is_valid_protocol(port)
