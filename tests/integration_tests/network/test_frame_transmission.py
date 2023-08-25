from primaite.simulator.network.hardware.base import Link, NIC, Node, Switch


def test_node_to_node_ping():
    """Tests two Nodes are able to ping each other."""
    # TODO Add actual checks. Manual check performed for now.
    node_a = Node(hostname="node_a")
    nic_a = NIC(ip_address="192.168.0.10", subnet_mask="255.255.255.0", gateway="192.168.0.1")
    node_a.connect_nic(nic_a)
    node_a.power_on()

    node_b = Node(hostname="node_b")
    nic_b = NIC(ip_address="192.168.0.11", subnet_mask="255.255.255.0", gateway="192.168.0.1")
    node_b.connect_nic(nic_b)
    node_b.power_on()

    Link(endpoint_a=nic_a, endpoint_b=nic_b)

    assert node_a.ping("192.168.0.11")


def test_multi_nic():
    """Tests that Nodes with multiple NICs can ping each other and the data go across the correct links."""
    # TODO Add actual checks. Manual check performed for now.
    node_a = Node(hostname="node_a")
    nic_a = NIC(ip_address="192.168.0.10", subnet_mask="255.255.255.0", gateway="192.168.0.1")
    node_a.connect_nic(nic_a)
    node_a.power_on()

    node_b = Node(hostname="node_b")
    nic_b1 = NIC(ip_address="192.168.0.11", subnet_mask="255.255.255.0", gateway="192.168.0.1")
    nic_b2 = NIC(ip_address="10.0.0.12", subnet_mask="255.0.0.0", gateway="10.0.0.1")
    node_b.connect_nic(nic_b1)
    node_b.connect_nic(nic_b2)
    node_b.power_on()

    node_c = Node(hostname="node_c")
    nic_c = NIC(ip_address="10.0.0.13", subnet_mask="255.0.0.0", gateway="10.0.0.1")
    node_c.connect_nic(nic_c)
    node_c.power_on()

    Link(endpoint_a=nic_a, endpoint_b=nic_b1)

    Link(endpoint_a=nic_b2, endpoint_b=nic_c)

    node_a.ping("192.168.0.11")

    assert node_c.ping("10.0.0.12")


def test_switched_network():
    """Tests a larges network of Nodes and Switches with one node pinging another."""
    # TODO Add actual checks. Manual check performed for now.
    pc_a = Node(hostname="pc_a")
    nic_a = NIC(ip_address="192.168.0.10", subnet_mask="255.255.255.0", gateway="192.168.0.1")
    pc_a.connect_nic(nic_a)
    pc_a.power_on()

    pc_b = Node(hostname="pc_b")
    nic_b = NIC(ip_address="192.168.0.11", subnet_mask="255.255.255.0", gateway="192.168.0.1")
    pc_b.connect_nic(nic_b)
    pc_b.power_on()

    pc_c = Node(hostname="pc_c")
    nic_c = NIC(ip_address="192.168.0.12", subnet_mask="255.255.255.0", gateway="192.168.0.1")
    pc_c.connect_nic(nic_c)
    pc_c.power_on()

    pc_d = Node(hostname="pc_d")
    nic_d = NIC(ip_address="192.168.0.13", subnet_mask="255.255.255.0", gateway="192.168.0.1")
    pc_d.connect_nic(nic_d)
    pc_d.power_on()

    switch_1 = Switch(hostname="switch_1", num_ports=6)
    switch_1.power_on()

    switch_2 = Switch(hostname="switch_2", num_ports=6)
    switch_2.power_on()

    link_nic_a_switch_1 = Link(endpoint_a=nic_a, endpoint_b=switch_1.switch_ports[1])
    link_nic_b_switch_1 = Link(endpoint_a=nic_b, endpoint_b=switch_1.switch_ports[2])
    link_nic_c_switch_2 = Link(endpoint_a=nic_c, endpoint_b=switch_2.switch_ports[1])
    link_nic_d_switch_2 = Link(endpoint_a=nic_d, endpoint_b=switch_2.switch_ports[2])
    link_switch_1_switch_2 = Link(endpoint_a=switch_1.switch_ports[6], endpoint_b=switch_2.switch_ports[6])

    assert pc_a.ping("192.168.0.13")
