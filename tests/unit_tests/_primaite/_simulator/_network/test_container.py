import json

import pytest

from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.computer import Computer
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.services.database.database_service import DatabaseService


@pytest.fixture(scope="function")
def network(example_network) -> Network:
    assert len(example_network.routers) is 1
    assert len(example_network.switches) is 2
    assert len(example_network.computers) is 2
    assert len(example_network.servers) is 2

    example_network.set_original_state()

    return example_network


def test_describe_state(example_network):
    """Test that describe state works."""
    state = example_network.describe_state()

    assert len(state["nodes"]) is 7
    assert len(state["links"]) is 6


def test_reset_network(example_network):
    """
    Test that the network is properly reset.

    TODO: make sure that once implemented - any installed/uninstalled services, processes, apps,
    etc are also removed/reinstalled

    """
    state_before = example_network.describe_state()

    client_1: Computer = example_network.get_node_by_hostname("client_1")
    server_1: Computer = example_network.get_node_by_hostname("server_1")

    assert client_1.operating_state is NodeOperatingState.ON
    assert server_1.operating_state is NodeOperatingState.ON

    client_1.power_off()
    assert client_1.operating_state is NodeOperatingState.SHUTTING_DOWN

    server_1.power_off()
    assert server_1.operating_state is NodeOperatingState.SHUTTING_DOWN

    assert example_network.describe_state() is not state_before

    example_network.reset_component_for_episode(episode=1)

    assert client_1.operating_state is NodeOperatingState.ON
    assert server_1.operating_state is NodeOperatingState.ON

    assert json.dumps(example_network.describe_state(), sort_keys=True, indent=2) == json.dumps(
        state_before, sort_keys=True, indent=2
    )


def test_creating_container():
    """Check that we can create a network container"""
    net = Network()
    assert net.nodes == {}
    assert net.links == {}
