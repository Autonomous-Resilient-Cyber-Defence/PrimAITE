# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from primaite.config.load import data_manipulation_config_path
from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.network.firewall import Firewall
from primaite.simulator.network.hardware.nodes.network.wireless_router import WirelessRouter
from tests.integration_tests.configuration_file_parsing import BASIC_CONFIG, DMZ_NETWORK, load_config


def test_example_config():
    """Test that the example config can be parsed properly."""
    game = load_config(data_manipulation_config_path())
    network: Network = game.simulation.network

    assert len(network.nodes) == 10  # 10 nodes in example network
    assert len(network.router_nodes) == 1  # 1 router in network
    assert len(network.switch_nodes) == 2  # 2 switches in network
    assert len(network.server_nodes) == 5  # 5 servers in network


def test_dmz_config():
    """Test that the DMZ network config can be parsed properly."""
    game = load_config(DMZ_NETWORK)

    network: Network = game.simulation.network

    assert len(network.nodes) == 9  # 9 nodes in network
    assert len(network.router_nodes) == 1  # 1 router in network
    assert len(network.firewall_nodes) == 1  # 1 firewall in network
    assert len(network.switch_nodes) == 3  # 3 switches in network
    assert len(network.server_nodes) == 2  # 2 servers in network


def test_basic_config():
    """Test that the basic_switched_network config can be parsed properly."""
    game = load_config(BASIC_CONFIG)
    network: Network = game.simulation.network
    assert len(network.nodes) == 4  # 4 nodes in network

    client_1: Computer = network.get_node_by_hostname("client_1")
    assert client_1.operating_state == NodeOperatingState.ON
    client_2: Computer = network.get_node_by_hostname("client_2")
    assert client_2.operating_state == NodeOperatingState.ON

    # client 3 should not be online
    client_3: Computer = network.get_node_by_hostname("client_3")
    assert client_3.operating_state == NodeOperatingState.OFF

    # Bandwidth should have non-default values

    for link in network.links:
        assert network.links[link].bandwidth == 200
