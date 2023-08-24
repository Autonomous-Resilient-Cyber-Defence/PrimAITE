import json

from primaite.simulator.network.container import NetworkContainer


def test_creating_container():
    """Check that we can create a network container"""
    net = NetworkContainer()
    assert net.nodes and net.links


def test_describe_state():
    """Check that we can describe network state without raising errors, and that the result is JSON serialisable."""
    net = NetworkContainer()
    state = net.describe_state()
    json.dumps(state)  # if this function call raises an error, the test fails, state was not JSON-serialisable
