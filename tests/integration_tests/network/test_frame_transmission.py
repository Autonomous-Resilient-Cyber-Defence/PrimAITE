# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.host_node import NIC
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.hardware.nodes.network.switch import Switch


def test_node_to_node_ping():
    """Tests two Computers are able to ping each other."""
    network = Network()

    client_1 = Computer(
        hostname="client_1",
        ip_address="192.168.1.10",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    client_1.power_on()

    server_1 = Server(
        hostname="server_1",
        ip_address="192.168.1.11",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    server_1.power_on()

    switch_1 = Switch(hostname="switch_1", start_up_duration=0)
    switch_1.power_on()

    network.connect(endpoint_a=client_1.network_interface[1], endpoint_b=switch_1.network_interface[1])
    network.connect(endpoint_a=server_1.network_interface[1], endpoint_b=switch_1.network_interface[2])

    assert client_1.ping("192.168.1.11")


def test_multi_nic():
    """Tests that Computers with multiple NICs can ping each other and the data go across the correct links."""
    network = Network()

    node_a = Computer(config=dict(hostname="node_a", ip_address="192.168.0.10", subnet_mask="255.255.255.0", start_up_duration=0))
    node_a.power_on()

    node_b = Computer(hostname="node_b", ip_address="192.168.0.11", subnet_mask="255.255.255.0", start_up_duration=0)
    node_b.power_on()
    node_b.connect_nic(NIC(ip_address="10.0.0.12", subnet_mask="255.0.0.0"))

    node_c = Computer(hostname="node_c", ip_address="10.0.0.13", subnet_mask="255.0.0.0", start_up_duration=0)
    node_c.power_on()

    network.connect(node_a.network_interface[1], node_b.network_interface[1])
    network.connect(node_b.network_interface[2], node_c.network_interface[1])

    assert node_a.ping(node_b.network_interface[1].ip_address)

    assert node_c.ping(node_b.network_interface[2].ip_address)

    assert not node_a.ping(node_b.network_interface[2].ip_address)

    assert not node_a.ping(node_c.network_interface[1].ip_address)
