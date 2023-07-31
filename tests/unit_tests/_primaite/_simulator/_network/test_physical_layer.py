import re

import pytest

from primaite.simulator.network.physical_layer import generate_mac_address


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
