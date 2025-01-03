# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.host_node import NIC
from primaite.simulator.network.hardware.nodes.host.server import Server


def test_network(example_network):
    network: Network = example_network
    client_1: Computer = network.get_node_by_hostname("client_1")
    client_2: Computer = network.get_node_by_hostname("client_2")
    server_1: Server = network.get_node_by_hostname("server_1")
    server_2: Server = network.get_node_by_hostname("server_2")

    assert client_1.ping(client_2.network_interface[1].ip_address)
    assert client_2.ping(client_1.network_interface[1].ip_address)

    assert server_1.ping(server_2.network_interface[1].ip_address)
    assert server_2.ping(server_1.network_interface[1].ip_address)

    assert client_1.ping(server_1.network_interface[1].ip_address)
    assert client_2.ping(server_1.network_interface[1].ip_address)
    assert client_1.ping(server_2.network_interface[1].ip_address)
    assert client_2.ping(server_2.network_interface[1].ip_address)


def test_adding_removing_nodes():
    """Check that we can create and add a node to a network."""
    net = Network()
    n1 = Computer(hostname="computer", ip_address="192.168.1.2", subnet_mask="255.255.255.0", start_up_duration=0)
    net.add_node(n1)
    assert n1.parent is net
    assert n1 in net

    net.remove_node(n1)
    assert n1.parent is None
    assert n1 not in net


def test_readding_node():
    """Check that warning is raised when readding a node."""
    net = Network()
    n1 = Computer(hostname="computer", ip_address="192.168.1.2", subnet_mask="255.255.255.0", start_up_duration=0)
    net.add_node(n1)
    net.add_node(n1)
    assert n1.parent is net
    assert n1 in net


def test_removing_nonexistent_node():
    """Check that warning is raised when trying to remove a node that is not in the network."""
    net = Network()
    n1 = Computer(hostname="computer1", ip_address="192.168.1.1", subnet_mask="255.255.255.0", start_up_duration=0)
    net.remove_node(n1)
    assert n1.parent is None
    assert n1 not in net


def test_connecting_nodes():
    """Check that two nodes on the network can be connected."""
    net = Network()
    n1 = Computer(hostname="computer1", ip_address="192.168.1.1", subnet_mask="255.255.255.0", start_up_duration=0)
    n2 = Computer(hostname="computer2", ip_address="192.168.1.2", subnet_mask="255.255.255.0", start_up_duration=0)

    net.add_node(n1)
    net.add_node(n2)

    net.connect(n1.network_interface[1], n2.network_interface[1])

    assert len(net.links) == 1
    link = list(net.links.values())[0]
    assert link in net
    assert link.parent is net


def test_connecting_node_to_itself_fails():
    net = Network()
    node = Computer(hostname="node_b", ip_address="192.168.0.11", subnet_mask="255.255.255.0", start_up_duration=0)
    node.power_on()
    node.connect_nic(NIC(ip_address="10.0.0.12", subnet_mask="255.0.0.0"))

    net.add_node(node)

    net.connect(node.network_interface[1], node.network_interface[2])

    assert node in net
    assert node.network_interface[1]._connected_link is None
    assert node.network_interface[2]._connected_link is None
    assert len(net.links) == 0


def test_disconnecting_nodes():
    net = Network()

    n1 = Computer(hostname="computer1", ip_address="192.168.1.1", subnet_mask="255.255.255.0", start_up_duration=0)
    n2 = Computer(hostname="computer2", ip_address="192.168.1.2", subnet_mask="255.255.255.0", start_up_duration=0)

    net.connect(n1.network_interface[1], n2.network_interface[1])
    assert len(net.links) == 1

    link = list(net.links.values())[0]
    net.remove_link(link)
    assert link not in net
    assert len(net.links) == 0
