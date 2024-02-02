from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.base import Link, NodeOperatingState
from primaite.simulator.network.hardware.nodes.computer import Computer
from primaite.simulator.network.hardware.nodes.server import Server
from primaite.simulator.network.hardware.nodes.switch import Switch


def test_switched_network(client_switch_server):
    """Tests a node can ping another node via the switch."""
    computer, switch, server = client_switch_server

    assert computer.ping(server.ethernet_port[1].ip_address)
