import pytest

from primaite.simulator.network.container import NetworkContainer
from primaite.simulator.network.hardware.base import Node


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
