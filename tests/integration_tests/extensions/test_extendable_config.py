# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
import os

from primaite.config.load import get_extended_config_path
from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from tests import TEST_ASSETS_ROOT
from tests.integration_tests.configuration_file_parsing import BASIC_CONFIG, DMZ_NETWORK, load_config
from tests.integration_tests.extensions.applications.extended_application import ExtendedApplication
from tests.integration_tests.extensions.nodes.giga_switch import GigaSwitch

# Import the extended components so that PrimAITE registers them
from tests.integration_tests.extensions.nodes.super_computer import SuperComputer
from tests.integration_tests.extensions.services.extended_service import ExtendedService

CONFIG_PATH = TEST_ASSETS_ROOT / "configs/extended_config.yaml"


def test_extended_example_config():
    """Test that the example config can be parsed properly."""
    game = load_config(CONFIG_PATH)
    network: Network = game.simulation.network

    assert len(network.nodes) == 10  # 10 nodes in example network
    assert len(network.computer_nodes) == 1
    assert len(network.router_nodes) == 1  # 1 router in network
    assert len(network.switch_nodes) == 1  # 1 switches in network
    assert len(network.server_nodes) == 5  # 5 servers in network

    extended_host = network.get_node_by_hostname("client_1")

    assert "extended-application" in extended_host.software_manager.software
    assert "extended-service" in extended_host.software_manager.software
