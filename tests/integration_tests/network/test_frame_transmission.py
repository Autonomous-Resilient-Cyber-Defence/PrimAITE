from src.primaite.simulator.network.hardware.base import Link, NIC, Node, NodeOperatingState


def test_node_to_node_ping():
    """Tests two Nodes are able to ping each other."""
    node_a = Node(hostname="node_a", operating_state=NodeOperatingState.ON)
    nic_a = NIC(ip_address="192.168.0.10", subnet_mask="255.255.255.0", operating_state=NodeOperatingState.ON)
    node_a.connect_nic(nic_a)

    node_b = Node(hostname="node_b", operating_state=NodeOperatingState.ON)
    nic_b = NIC(ip_address="192.168.0.11", subnet_mask="255.255.255.0")
    node_b.connect_nic(nic_b)

    Link(endpoint_a=nic_a, endpoint_b=nic_b)

    assert node_a.ping("192.168.0.11")


def test_multi_nic():
    """Tests that Nodes with multiple NICs can ping each other and the data go across the correct links."""
    node_a = Node(hostname="node_a", operating_state=NodeOperatingState.ON)
    nic_a = NIC(ip_address="192.168.0.10", subnet_mask="255.255.255.0")
    node_a.connect_nic(nic_a)

    node_b = Node(hostname="node_b", operating_state=NodeOperatingState.ON)
    nic_b1 = NIC(ip_address="192.168.0.11", subnet_mask="255.255.255.0")
    nic_b2 = NIC(ip_address="10.0.0.12", subnet_mask="255.0.0.0")
    node_b.connect_nic(nic_b1)
    node_b.connect_nic(nic_b2)

    node_c = Node(hostname="node_c", operating_state=NodeOperatingState.ON)
    nic_c = NIC(ip_address="10.0.0.13", subnet_mask="255.0.0.0")
    node_c.connect_nic(nic_c)

    Link(endpoint_a=nic_a, endpoint_b=nic_b1)

    Link(endpoint_a=nic_b2, endpoint_b=nic_c)

    node_a.ping("192.168.0.11")

    assert node_c.ping("10.0.0.12")
