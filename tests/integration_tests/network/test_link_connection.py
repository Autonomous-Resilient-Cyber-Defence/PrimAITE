from primaite.simulator.network.hardware.base import Link, NIC, Node


def test_link_up():
    """Tests Nodes, NICs, and Links can all be connected and be in an enabled/up state."""
    node_a = Node(hostname="node_a")
    nic_a = NIC(ip_address="192.168.0.10", subnet_mask="255.255.255.0", gateway="192.168.0.1")
    node_a.connect_nic(nic_a)
    node_a.power_on()
    assert nic_a.enabled

    node_b = Node(hostname="node_b")
    nic_b = NIC(ip_address="192.168.0.11", subnet_mask="255.255.255.0", gateway="192.168.0.1")
    node_b.connect_nic(nic_b)
    node_b.power_on()

    assert nic_b.enabled

    link = Link(endpoint_a=nic_a, endpoint_b=nic_b)

    assert link.is_up
