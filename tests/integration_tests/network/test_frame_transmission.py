from primaite.simulator.network.hardware.base import Link, NIC, Node


def test_node_to_node_ping():
    node_a = Node(hostname="node_a")
    nic_a = NIC(ip_address="192.168.0.10", subnet_mask="255.255.255.0", gateway="192.168.0.1")
    node_a.connect_nic(nic_a)
    node_a.turn_on()

    node_b = Node(hostname="node_b")
    nic_b = NIC(ip_address="192.168.0.11", subnet_mask="255.255.255.0", gateway="192.168.0.1")
    node_b.connect_nic(nic_b)
    node_b.turn_on()

    Link(endpoint_a=nic_a, endpoint_b=nic_b)

    assert node_a.ping("192.168.0.11")

    node_a.turn_off()

    assert not node_a.ping("192.168.0.11")

    node_a.turn_on()

    assert node_a.ping("192.168.0.11")
