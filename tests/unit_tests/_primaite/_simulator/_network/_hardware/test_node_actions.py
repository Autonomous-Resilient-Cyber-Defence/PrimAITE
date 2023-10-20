import pytest

from primaite.simulator.network.hardware.base import Node, NodeOperatingState


@pytest.fixture
def node() -> Node:
    return Node(hostname="test")


def test_node_startup(node):
    assert node.operating_state == NodeOperatingState.OFF
    node.apply_request(["startup"])
    assert node.operating_state == NodeOperatingState.ON


def test_node_shutdown(node):
    assert node.operating_state == NodeOperatingState.OFF
    node.apply_request(["startup"])
    assert node.operating_state == NodeOperatingState.ON

    node.apply_request(["shutdown"])
    assert node.operating_state == NodeOperatingState.OFF
