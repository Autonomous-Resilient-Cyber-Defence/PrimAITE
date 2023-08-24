import pytest

from primaite.simulator.network.container import NetworkContainer
from primaite.simulator.network.hardware.base import NIC, Node


def test_adding_removing_nodes():
    """Check that we can create and add a node to a network."""
    net = NetworkContainer()
    n1 = Node(hostname="computer")
    net.add_node(n1)
    assert n1.parent is net
    assert n1 in net

    net.remove_node(n1)
    assert n1.parent is None
    assert n1 not in net


def test_readding_node():
    """Check that warning is raised when readding a node."""
    net = NetworkContainer()
    n1 = Node(hostname="computer")
    net.add_node(n1)
    with pytest.raises(RuntimeWarning):
        net.add_node(n1)
    assert n1.parent is net
    assert n1 in net


def test_removing_nonexistent_node():
    """Check that warning is raised when trying to remove a node that is not in the network."""
    net = NetworkContainer()
    n1 = Node(hostname="computer")
    with pytest.raises(RuntimeWarning):
        net.remove_node(n1)
    assert n1.parent is None
    assert n1 not in net


def test_connecting_nodes():
    """Check that two nodes on the network can be connected."""
    net = NetworkContainer()
    n1 = Node(hostname="computer")
    n1_nic = NIC(ip_address="120.30.0.1", gateway="192.168.0.1", subnet_mask="255.255.255.0")
    n1.connect_nic(n1_nic)
    n2 = Node(hostname="server")
    n2_nic = NIC(ip_address="120.30.0.2", gateway="192.168.0.1", subnet_mask="255.255.255.0")
    n2.connect_nic(n2_nic)

    net.add_node(n1)
    net.add_node(n2)

    net.connect_nodes(n1.nics[n1_nic.uuid], n2.nics[n2_nic.uuid], bandwidth=30)

    assert len(net.links) == 1
    link = list(net.links.values())[0]
    assert link in net
    assert link.parent is net


def test_connecting_node_to_itself():
    net = NetworkContainer()
    node = Node(hostname="computer")
    nic1 = NIC(ip_address="120.30.0.1", gateway="192.168.0.1", subnet_mask="255.255.255.0")
    node.connect_nic(nic1)
    nic2 = NIC(ip_address="120.30.0.2", gateway="192.168.0.1", subnet_mask="255.255.255.0")
    node.connect_nic(nic2)

    net.add_node(node)

    with pytest.raises(RuntimeError):
        net.connect_nodes(node.nics[nic1.uuid], node.nics[nic2.uuid], bandwidth=30)

    assert node in net
    assert nic1.connected_link is None
    assert nic2.connected_link is None
    assert len(net.links) == 0


def test_disconnecting_nodes():
    ...
