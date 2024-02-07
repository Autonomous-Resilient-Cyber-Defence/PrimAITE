from pathlib import Path
from typing import Union

import yaml

from primaite.config.load import example_config_path
from primaite.game.agent.data_manipulation_bot import DataManipulationAgent
from primaite.game.agent.interface import ProxyAgent, RandomAgent
from primaite.game.game import APPLICATION_TYPES_MAPPING, PrimaiteGame, SERVICE_TYPES_MAPPING
from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.computer import Computer
from primaite.simulator.system.applications.web_browser import WebBrowser
from primaite.simulator.system.services.dns.dns_client import DNSClient
from primaite.simulator.system.services.ftp.ftp_client import FTPClient
from tests import TEST_ASSETS_ROOT

BASIC_CONFIG = TEST_ASSETS_ROOT / "configs/basic_switched_network.yaml"


def load_config(config_path: Union[str, Path]) -> PrimaiteGame:
    """Returns a PrimaiteGame object which loads the contents of a given yaml path."""
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    return PrimaiteGame.from_config(cfg)


def test_example_config():
    """Test that the example config can be parsed properly."""
    game = load_config(example_config_path())

    assert len(game.agents) == 3  # red, blue and green agent

    # green agent
    assert game.agents[0].agent_name == "client_2_green_user"
    assert isinstance(game.agents[0], RandomAgent)

    # red agent
    assert game.agents[1].agent_name == "client_1_data_manipulation_red_bot"
    assert isinstance(game.agents[1], DataManipulationAgent)

    # blue agent
    assert game.agents[2].agent_name == "defender"
    assert isinstance(game.agents[2], ProxyAgent)

    network: Network = game.simulation.network

    assert len(network.nodes) == 10  # 10 nodes in example network
    assert len(network.routers) == 1  # 1 router in network
    assert len(network.switches) == 2  # 2 switches in network
    assert len(network.servers) == 5  # 5 servers in network


def test_node_software_install():
    """Test that software can be installed on a node."""
    game = load_config(BASIC_CONFIG)

    client_1: Computer = game.simulation.network.get_node_by_hostname("client_1")
    client_2: Computer = game.simulation.network.get_node_by_hostname("client_2")

    system_software = {DNSClient, FTPClient, WebBrowser}

    # check that system software is installed on client 1
    for software in system_software:
        assert client_1.software_manager.software.get(software.__name__) is not None

    # check that system software is installed on client 2
    for software in system_software:
        assert client_2.software_manager.software.get(software.__name__) is not None

    # check that applications have been installed on client 1
    for applications in APPLICATION_TYPES_MAPPING:
        assert client_1.software_manager.software.get(applications) is not None

    # check that services have been installed on client 1
    # for service in SERVICE_TYPES_MAPPING:
    #     assert client_1.software_manager.software.get(service) is not None
