import json

import pytest

from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.base import Link, Node
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.host.computer import Computer


def filter_keys_nested_item(data, keys):
    stack = [(data, {})]
    while stack:
        current, filtered = stack.pop()
        if isinstance(current, dict):
            for k, v in current.items():
                if k in keys:
                    filtered[k] = filter_keys_nested_item(v, keys)
                elif isinstance(v, (dict, list)):
                    stack.append((v, {}))
        elif isinstance(current, list):
            for item in current:
                stack.append((item, {}))
    return filtered


@pytest.fixture(scope="function")
def network(example_network) -> Network:
    assert len(example_network.routers) is 1
    assert len(example_network.switches) is 2
    assert len(example_network.computers) is 2
    assert len(example_network.servers) is 2

    example_network.set_original_state()
    example_network.show()

    return example_network


def test_describe_state(network):
    """Test that describe state works."""
    state = network.describe_state()

    assert len(state["nodes"]) is 7
    assert len(state["links"]) is 6


def test_reset_network(network):
    """
    Test that the network is properly reset.

    TODO: make sure that once implemented - any installed/uninstalled services, processes, apps,
    etc are also removed/reinstalled

    """
    state_before = network.describe_state()

    client_1: Computer = network.get_node_by_hostname("client_1")
    server_1: Computer = network.get_node_by_hostname("server_1")

    assert client_1.operating_state is NodeOperatingState.ON
    assert server_1.operating_state is NodeOperatingState.ON

    client_1.power_off()
    assert client_1.operating_state is NodeOperatingState.SHUTTING_DOWN

    server_1.power_off()
    assert server_1.operating_state is NodeOperatingState.SHUTTING_DOWN

    assert network.describe_state() != state_before

    network.reset_component_for_episode(episode=1)

    assert client_1.operating_state is NodeOperatingState.ON
    assert server_1.operating_state is NodeOperatingState.ON
    # don't worry if UUIDs change
    a = filter_keys_nested_item(json.dumps(network.describe_state(), sort_keys=True, indent=2), ["uuid"])
    b = filter_keys_nested_item(json.dumps(state_before, sort_keys=True, indent=2), ["uuid"])
    assert a == b


def test_creating_container():
    """Check that we can create a network container"""
    net = Network()
    assert net.nodes == {}
    assert net.links == {}
    net.show()


def test_apply_timestep_to_nodes(network):
    """Calling apply_timestep on the network should apply to the nodes within it."""
    client_1: Computer = network.get_node_by_hostname("client_1")
    assert client_1.operating_state is NodeOperatingState.ON

    client_1.power_off()
    assert client_1.operating_state is NodeOperatingState.SHUTTING_DOWN

    for i in range(client_1.shut_down_duration + 1):
        network.apply_timestep(timestep=i)

    assert client_1.operating_state is NodeOperatingState.OFF

    network.apply_timestep(client_1.shut_down_duration + 2)
    assert client_1.operating_state is NodeOperatingState.OFF


def test_removing_node_that_does_not_exist(network):
    """Node that does not exist on network should not affect existing nodes."""
    assert len(network.nodes) is 7

    network.remove_node(Computer(hostname="new_node", ip_address="192.168.1.2", subnet_mask="255.255.255.0"))
    assert len(network.nodes) is 7


def test_remove_node(network):
    """Remove node should remove the correct node."""
    assert len(network.nodes) is 7

    client_1: Computer = network.get_node_by_hostname("client_1")
    network.remove_node(client_1)

    assert network.get_node_by_hostname("client_1") is None
    assert len(network.nodes) is 6


def test_remove_link(network):
    """Remove link should remove the correct link."""
    assert len(network.links) is 6
    link: Link = network.links.get(next(iter(network.links)))

    network.remove_link(link)
    assert len(network.links) is 5
    assert network.links.get(link.uuid) is None
