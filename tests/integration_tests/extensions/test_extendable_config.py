# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from primaite.config.load import get_extended_config_path
from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from tests.integration_tests.configuration_file_parsing import BASIC_CONFIG, DMZ_NETWORK, load_config
import os

# Import the extended components so that PrimAITE registers them
from tests.integration_tests.extensions.nodes.super_computer import SuperComputer
from tests.integration_tests.extensions.nodes.giga_switch import GigaSwitch
from tests.integration_tests.extensions.services.extended_service import ExtendedService
from tests.integration_tests.extensions.applications.extended_application import ExtendedApplication


def test_extended_example_config():

    """Test that the example config can be parsed properly."""
    config_path = os.path.join( "tests", "assets", "configs", "extended_config.yaml")
    game = load_config(config_path)
    network: Network = game.simulation.network

    assert len(network.nodes) == 10  # 10 nodes in example network
    assert len(network.computer_nodes) == 1
    assert len(network.router_nodes) == 1  # 1 router in network
    assert len(network.switch_nodes) == 1  # 1 switches in network
    assert len(network.server_nodes) == 5  # 5 servers in network
    assert len(network.extended_hostnodes) == 1 # One extended node based on HostNode
    assert len(network.extended_networknodes) == 1 # One extended node based on NetworkNode

    assert 'ExtendedApplication' in network.extended_hostnodes[0].software_manager.software
    assert 'ExtendedService' in network.extended_hostnodes[0].software_manager.software
