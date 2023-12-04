from primaite.simulator.network.hardware.base import Link, NIC, Node, NodeOperatingState


def test_link_up():
    """Tests Nodes, NICs, and Links can all be connected and be in an enabled/up state."""
    node_a = Node(hostname="node_a", operating_state=NodeOperatingState.ON)
    nic_a = NIC(ip_address="192.168.0.10", subnet_mask="255.255.255.0")
    node_a.connect_nic(nic_a)

    node_b = Node(hostname="node_b", operating_state=NodeOperatingState.ON)
    nic_b = NIC(ip_address="192.168.0.11", subnet_mask="255.255.255.0")
    node_b.connect_nic(nic_b)

    link = Link(endpoint_a=nic_a, endpoint_b=nic_b)

    assert nic_a.enabled
    assert nic_b.enabled
    assert link.is_up


def test_ping_between_computer_and_server(client_server):
    computer, server = client_server

    assert computer.ping(target_ip_address=server.nics[next(iter(server.nics))].ip_address)
