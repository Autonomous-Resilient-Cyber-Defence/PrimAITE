from primaite.simulator.network.hardware.base import Node, NIC, Link
from primaite.simulator.network.hardware.nodes.router import Router


def test_ping_fails_with_no_route():
    """Tests a larges network of Nodes and Switches with one node pinging another."""
    pc_a = Node(hostname="pc_a")
    nic_a = NIC(ip_address="192.168.0.10", subnet_mask="255.255.255.0", gateway="192.168.0.1")
    pc_a.connect_nic(nic_a)
    pc_a.power_on()

    pc_b = Node(hostname="pc_b")
    nic_b = NIC(ip_address="192.168.1.10", subnet_mask="255.255.255.0", gateway="192.168.1.1")
    pc_b.connect_nic(nic_b)
    pc_b.power_on()

    router_1 = Router(hostname="router_1")
    router_1.configure_port(1, "192.168.0.1", "255.255.255.0")
    router_1.configure_port(2, "192.168.1.1", "255.255.255.0")

    router_1.power_on()
    router_1.show()

    link_nic_a_router_1 = Link(endpoint_a=nic_a, endpoint_b=router_1.ethernet_ports[1])
    link_nic_b_router_1 = Link(endpoint_a=nic_b, endpoint_b=router_1.ethernet_ports[2])
    router_1.power_on()
    #assert pc_a.ping("192.168.1.10")