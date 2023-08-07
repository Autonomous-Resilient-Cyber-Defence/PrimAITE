from primaite.simulator.network.hardware.base import Link, NIC, Node, Switch


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


def test_multi_nic():
    node_a = Node(hostname="node_a")
    nic_a = NIC(ip_address="192.168.0.10", subnet_mask="255.255.255.0", gateway="192.168.0.1")
    node_a.connect_nic(nic_a)
    node_a.turn_on()

    node_b = Node(hostname="node_b")
    nic_b1 = NIC(ip_address="192.168.0.11", subnet_mask="255.255.255.0", gateway="192.168.0.1")
    nic_b2 = NIC(ip_address="10.0.0.12", subnet_mask="255.0.0.0", gateway="10.0.0.1")
    node_b.connect_nic(nic_b1)
    node_b.connect_nic(nic_b2)
    node_b.turn_on()

    node_c = Node(hostname="node_c")
    nic_c = NIC(ip_address="10.0.0.13", subnet_mask="255.0.0.0", gateway="10.0.0.1")
    node_c.connect_nic(nic_c)
    node_c.turn_on()

    Link(endpoint_a=nic_a, endpoint_b=nic_b1)

    Link(endpoint_a=nic_b2, endpoint_b=nic_c)

    node_a.ping("192.168.0.11")

    node_c.ping("10.0.0.12")


def test_switched_network():
    node_a = Node(hostname="node_a")
    nic_a = NIC(ip_address="192.168.0.10", subnet_mask="255.255.255.0", gateway="192.168.0.1")
    node_a.connect_nic(nic_a)
    node_a.turn_on()

    node_b = Node(hostname="node_b")
    nic_b = NIC(ip_address="192.168.0.11", subnet_mask="255.255.255.0", gateway="192.168.0.1")
    node_b.connect_nic(nic_b)
    node_b.turn_on()

    node_c = Node(hostname="node_c")
    nic_c = NIC(ip_address="192.168.0.12", subnet_mask="255.255.255.0", gateway="192.168.0.1")
    node_c.connect_nic(nic_c)
    node_c.turn_on()

    switch_1 = Switch(hostname="switch_1")
    switch_1.turn_on()

    switch_2 = Switch(hostname="switch_2")
    switch_2.turn_on()

    Link(endpoint_a=nic_a, endpoint_b=switch_1.switch_ports[1])
    Link(endpoint_a=nic_b, endpoint_b=switch_1.switch_ports[2])
    Link(endpoint_a=switch_1.switch_ports[24], endpoint_b=switch_2.switch_ports[24])
    Link(endpoint_a=nic_c, endpoint_b=switch_2.switch_ports[1])

    node_a.ping("192.168.0.12")
