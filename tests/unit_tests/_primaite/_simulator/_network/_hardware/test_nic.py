import re
from ipaddress import IPv4Address

import pytest

from primaite.simulator.network.hardware.base import generate_mac_address, NIC


def test_mac_address_generation():
    """Tests random mac address generation."""
    mac_address = generate_mac_address()
    assert re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac_address)


def test_mac_address_with_oui():
    """Tests random mac address generation with oui."""
    oui = "aa:bb:cc"
    mac_address = generate_mac_address(oui=oui)
    assert re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac_address)
    assert mac_address[:8] == oui


def test_invalid_oui_mac_address():
    """Tests random mac address generation fails with invalid oui."""
    invalid_oui = "aa-bb-cc"
    with pytest.raises(ValueError):
        generate_mac_address(oui=invalid_oui)


def test_nic_ip_address_type_conversion():
    """Tests NIC IP and gateway address is converted to IPv4Address is originally a string."""
    nic = NIC(
        ip_address="192.168.1.2",
        subnet_mask="255.255.255.0",
        gateway="192.168.0.1",
    )
    assert isinstance(nic.ip_address, IPv4Address)
    assert isinstance(nic.gateway, IPv4Address)


def test_nic_deserialize():
    """Tests NIC serialization and deserialization."""
    nic = NIC(
        ip_address="192.168.1.2",
        subnet_mask="255.255.255.0",
        gateway="192.168.0.1",
    )

    nic_json = nic.model_dump_json()
    deserialized_nic = NIC.model_validate_json(nic_json)
    assert nic == deserialized_nic


def test_nic_ip_address_as_gateway_fails():
    """Tests NIC creation fails if ip address is the same as the gateway."""
    with pytest.raises(ValueError):
        NIC(
            ip_address="192.168.0.1",
            subnet_mask="255.255.255.0",
            gateway="192.168.0.1",
        )


def test_nic_ip_address_as_network_address_fails():
    """Tests NIC creation fails if ip address and subnet mask are a network address."""
    with pytest.raises(ValueError):
        NIC(
            ip_address="192.168.0.0",
            subnet_mask="255.255.255.0",
            gateway="192.168.0.1",
        )
