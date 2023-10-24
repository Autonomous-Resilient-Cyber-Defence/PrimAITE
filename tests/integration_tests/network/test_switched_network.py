from primaite.simulator.network.hardware.base import Link, NodeOperatingState
from primaite.simulator.network.hardware.nodes.computer import Computer
from primaite.simulator.network.hardware.nodes.server import Server
from primaite.simulator.network.hardware.nodes.switch import Switch


def test_switched_network():
    """Tests a node can ping another node via the switch."""
    client_1 = Computer(
        hostname="client_1",
        ip_address="192.168.1.10",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.0",
        operating_state=NodeOperatingState.ON,
    )

    server_1 = Server(
        hostname=" server_1",
        ip_address="192.168.1.11",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.11",
        operating_state=NodeOperatingState.ON,
    )

    switch_1 = Switch(hostname="switch_1", num_ports=6, operating_state=NodeOperatingState.ON)

    Link(endpoint_a=client_1.ethernet_port[1], endpoint_b=switch_1.switch_ports[1])
    Link(endpoint_a=server_1.ethernet_port[1], endpoint_b=switch_1.switch_ports[2])

    assert client_1.ping("192.168.1.11")
