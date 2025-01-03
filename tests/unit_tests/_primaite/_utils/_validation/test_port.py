# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
import pytest

from primaite.utils.validation.port import is_valid_port, Port, PORT_LOOKUP, port_validator


def test_port_conversion():
    valid_port_lookup = {k: v for k, v in PORT_LOOKUP.items() if k != "UNUSED"}
    for port_name, port_val in valid_port_lookup.items():
        assert port_validator(port_name) == port_val
        assert is_valid_port(port_name)


def test_port_passthrough():
    valid_port_lookup = {k: v for k, v in PORT_LOOKUP.items() if k != "UNUSED"}
    for port_val in valid_port_lookup.values():
        assert port_validator(port_val) == port_val
        assert is_valid_port(port_val)


def test_invalid_ports():
    for port in (999999, -20, 3.214, "NONEXISTENT_PORT"):
        with pytest.raises(ValueError):
            port_validator(port)
        assert not is_valid_port(port)
