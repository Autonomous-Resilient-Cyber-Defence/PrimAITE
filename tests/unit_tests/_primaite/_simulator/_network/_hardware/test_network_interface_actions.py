# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
import pytest

from primaite.simulator.network.hardware.base import NetworkInterface, Node
from primaite.simulator.network.hardware.nodes.host.computer import Computer


@pytest.fixture
def node() -> Node:
    return Computer(hostname="test", ip_address="192.168.1.2", subnet_mask="255.255.255.0")


def test_nic_enabled_validator(node):
    """Test the NetworkInterface enabled validator."""
    network_interface = node.network_interface[1]
    validator = NetworkInterface._EnabledValidator(network_interface=network_interface)

    assert validator(request=[], context={}) is False  # not enabled

    network_interface.enabled = True

    assert validator(request=[], context={})  # enabled


def test_nic_disabled_validator(node):
    """Test the NetworkInterface enabled validator."""
    network_interface = node.network_interface[1]
    validator = NetworkInterface._DisabledValidator(network_interface=network_interface)

    assert validator(request=[], context={})  # not enabled

    network_interface.enabled = True

    assert validator(request=[], context={}) is False  # enabled
