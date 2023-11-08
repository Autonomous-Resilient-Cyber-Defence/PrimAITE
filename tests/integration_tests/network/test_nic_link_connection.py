import pytest

from src.primaite.simulator.network.hardware.base import Link, NIC


def test_link_fails_with_same_nic():
    """Tests Link creation fails with endpoint_a and endpoint_b are the same NIC."""
    with pytest.raises(ValueError):
        nic_a = NIC(ip_address="192.168.1.2", subnet_mask="255.255.255.0")
        Link(endpoint_a=nic_a, endpoint_b=nic_a)
