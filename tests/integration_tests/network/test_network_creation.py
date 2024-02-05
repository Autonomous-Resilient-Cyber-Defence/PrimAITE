from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.base import Node
from primaite.simulator.network.hardware.nodes.host.computer import Computer
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
    n1 = Node(hostname="computer")
    net.add_node(n1)
    assert n1.parent is net
    assert n1 in net

    net.remove_node(n1)
    assert n1.parent is None
    assert n1 not in net


def test_readding_node():
    """Check that warning is raised when readding a node."""
    net = Network()
    n1 = Node(hostname="computer")
    net.add_node(n1)
    net.add_node(n1)
    assert n1.parent is net
    assert n1 in net


def test_removing_nonexistent_node():
    """Check that warning is raised when trying to remove a node that is not in the network."""
    net = Network()
    n1 = Node(hostname="computer")
    net.remove_node(n1)
    assert n1.parent is None
    assert n1 not in net


def test_connecting_nodes():
    """Check that two nodes on the network can be connected."""
    net = Network()
    n1 = Node(hostname="computer")
    n1_nic = NIC(ip_address="120.30.0.1", gateway="192.168.0.1", subnet_mask="255.255.255.0")
    n1.connect_nic(n1_nic)
    n2 = Node(hostname="server")
    n2_nic = NIC(ip_address="120.30.0.2", gateway="192.168.0.1", subnet_mask="255.255.255.0")
    n2.connect_nic(n2_nic)

    net.add_node(n1)
    net.add_node(n2)

    net.connect(n1.network_interfaces[n1_nic.uuid], n2.network_interfaces[n2_nic.uuid], bandwidth=30)

    assert len(net.links) == 1
    link = list(net.links.values())[0]
    assert link in net
    assert link.parent is net


def test_connecting_node_to_itself():
    net = Network()
    node = Node(hostname="computer")
    nic1 = NIC(ip_address="120.30.0.1", gateway="192.168.0.1", subnet_mask="255.255.255.0")
    node.connect_nic(nic1)
    nic2 = NIC(ip_address="120.30.0.2", gateway="192.168.0.1", subnet_mask="255.255.255.0")
    node.connect_nic(nic2)

    net.add_node(node)

    net.connect(node.network_interfaces[nic1.uuid], node.network_interfaces[nic2.uuid], bandwidth=30)

    assert node in net
    assert nic1._connected_link is None
    assert nic2._connected_link is None
    assert len(net.links) == 0


def test_disconnecting_nodes():
    net = Network()

    n1 = Node(hostname="computer")
    n1_nic = NIC(ip_address="120.30.0.1", gateway="192.168.0.1", subnet_mask="255.255.255.0")
    n1.connect_nic(n1_nic)
    net.add_node(n1)

    n2 = Node(hostname="server")
    n2_nic = NIC(ip_address="120.30.0.2", gateway="192.168.0.1", subnet_mask="255.255.255.0")
    n2.connect_nic(n2_nic)
    net.add_node(n2)

    net.connect(n1.network_interfaces[n1_nic.uuid], n2.network_interfaces[n2_nic.uuid], bandwidth=30)
    assert len(net.links) == 1

    link = list(net.links.values())[0]
    net.remove_link(link)
    assert link not in net
    assert len(net.links) == 0
