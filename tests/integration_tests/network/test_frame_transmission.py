from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.computer import Computer
from primaite.simulator.network.hardware.nodes.server import Server
from primaite.simulator.network.hardware.nodes.switch import Switch



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

    network.connect(endpoint_a=client_1.ethernet_port[1], endpoint_b=switch_1.switch_ports[1])
    network.connect(endpoint_a=server_1.ethernet_port[1], endpoint_b=switch_1.switch_ports[2])

    assert client_1.ping("192.168.1.11")


def test_multi_nic():
    """Tests that Computers with multiple NICs can ping each other and the data go across the correct links."""
    node_a = Computer(hostname="node_a", operating_state=ComputerOperatingState.ON)
    nic_a = NIC(ip_address="192.168.0.10", subnet_mask="255.255.255.0")
    node_a.connect_nic(nic_a)

    node_b = Computer(hostname="node_b", operating_state=ComputerOperatingState.ON)
    nic_b1 = NIC(ip_address="192.168.0.11", subnet_mask="255.255.255.0")
    nic_b2 = NIC(ip_address="10.0.0.12", subnet_mask="255.0.0.0")
    node_b.connect_nic(nic_b1)
    node_b.connect_nic(nic_b2)

    node_c = Computer(hostname="node_c", operating_state=ComputerOperatingState.ON)
    nic_c = NIC(ip_address="10.0.0.13", subnet_mask="255.0.0.0")
    node_c.connect_nic(nic_c)

    Link(endpoint_a=nic_a, endpoint_b=nic_b1)

    Link(endpoint_a=nic_b2, endpoint_b=nic_c)

    node_a.ping("192.168.0.11")

    assert node_c.ping("10.0.0.12")
