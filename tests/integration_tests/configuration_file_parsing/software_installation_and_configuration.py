# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from ipaddress import IPv4Address
from pathlib import Path
from typing import Union

import yaml

from primaite.config.load import data_manipulation_config_path
from primaite.game.agent.scripted_agents.data_manipulation_bot import DataManipulationAgent
from primaite.game.agent.scripted_agents.interface import ProxyAgent
from primaite.game.agent.scripted_agents.probabilistic_agent import ProbabilisticAgent
from primaite.game.game import PrimaiteGame, SERVICE_TYPES_MAPPING
from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.system.applications.application import Application
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.applications.red_applications.data_manipulation_bot import DataManipulationBot
from primaite.simulator.system.applications.red_applications.dos_bot import DoSBot
from primaite.simulator.system.applications.web_browser import WebBrowser
from primaite.simulator.system.services.database.database_service import DatabaseService
from primaite.simulator.system.services.dns.dns_client import DNSClient
from primaite.simulator.system.services.dns.dns_server import DNSServer
from primaite.simulator.system.services.ftp.ftp_client import FTPClient
from primaite.simulator.system.services.ftp.ftp_server import FTPServer
from primaite.simulator.system.services.ntp.ntp_client import NTPClient
from primaite.simulator.system.services.ntp.ntp_server import NTPServer
from primaite.simulator.system.services.web_server.web_server import WebServer
from tests import TEST_ASSETS_ROOT

BASIC_CONFIG = TEST_ASSETS_ROOT / "configs/basic_switched_network.yaml"


def load_config(config_path: Union[str, Path]) -> PrimaiteGame:
    """Returns a PrimaiteGame object which loads the contents of a given yaml path."""
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    return PrimaiteGame.from_config(cfg)


def test_example_config():
    """Test that the example config can be parsed properly."""
    game = load_config(data_manipulation_config_path())

    assert len(game.agents) == 4  # red, blue and 2 green agents

    # green agent 1
    assert "client_2_green_user" in game.agents
    assert isinstance(game.agents["client_2_green_user"], ProbabilisticAgent)

    # green agent 2
    assert "client_1_green_user" in game.agents
    assert isinstance(game.agents["client_1_green_user"], ProbabilisticAgent)

    # red agent
    assert "data_manipulation_attacker" in game.agents
    assert isinstance(game.agents["data_manipulation_attacker"], DataManipulationAgent)

    # blue agent
    assert "defender" in game.agents
    assert isinstance(game.agents["defender"], ProxyAgent)

    network: Network = game.simulation.network

    assert len(network.nodes) == 10  # 10 nodes in example network
    assert len(network.router_nodes) == 1  # 1 router in network
    assert len(network.switch_nodes) == 2  # 2 switches in network
    assert len(network.server_nodes) == 5  # 5 servers in network


def test_node_software_install():
    """Test that software can be installed on a node."""
    game = load_config(BASIC_CONFIG)

    client_1: Computer = game.simulation.network.get_node_by_hostname("client_1")
    client_2: Computer = game.simulation.network.get_node_by_hostname("client_2")

    system_software = {DNSClient, FTPClient, NTPClient, WebBrowser}

    # check that system software is installed on client 1
    for software in system_software:
        assert client_1.software_manager.software.get(software.__name__) is not None

    # check that system software is installed on client 2
    for software in system_software:
        assert client_2.software_manager.software.get(software.__name__) is not None

    # check that applications have been installed on client 1
    for applications in Application._registry:
        assert client_1.software_manager.software.get(applications) is not None

    # check that services have been installed on client 1
    for service in SERVICE_TYPES_MAPPING:
        assert client_1.software_manager.software.get(service) is not None


def test_web_browser_install():
    """Test that the web browser can be configured via config."""
    game = load_config(BASIC_CONFIG)
    client_1: Computer = game.simulation.network.get_node_by_hostname("client_1")

    web_browser: WebBrowser = client_1.software_manager.software.get("WebBrowser")

    assert web_browser.target_url == "http://arcd.com/users/"


def test_database_client_install():
    """Test that the Database Client service can be configured via config."""
    game = load_config(BASIC_CONFIG)
    client_1: Computer = game.simulation.network.get_node_by_hostname("client_1")

    database_client: DatabaseClient = client_1.software_manager.software.get("DatabaseClient")

    assert database_client.server_ip_address == IPv4Address("192.168.1.10")
    assert database_client.server_password == "arcd"


def test_data_manipulation_bot_install():
    """Test that the data manipulation bot can be configured via config."""
    game = load_config(BASIC_CONFIG)
    client_1: Computer = game.simulation.network.get_node_by_hostname("client_1")

    data_manipulation_bot: DataManipulationBot = client_1.software_manager.software.get("DataManipulationBot")

    assert data_manipulation_bot.server_ip_address == IPv4Address("192.168.1.21")
    assert data_manipulation_bot.payload == "DELETE"
    assert data_manipulation_bot.data_manipulation_p_of_success == 0.8
    assert data_manipulation_bot.port_scan_p_of_success == 0.8
    assert data_manipulation_bot.server_password == "arcd"


def test_dos_bot_install():
    """Test that the denial of service bot can be configured via config."""
    game = load_config(BASIC_CONFIG)
    client_1: Computer = game.simulation.network.get_node_by_hostname("client_1")

    dos_bot: DoSBot = client_1.software_manager.software.get("DoSBot")

    assert dos_bot.target_ip_address == IPv4Address("192.168.10.21")
    assert dos_bot.payload == "SPOOF DATA"
    assert dos_bot.port_scan_p_of_success == 0.8
    assert dos_bot.dos_intensity == 1.0  # default
    assert dos_bot.max_sessions == 1000  # default
    assert dos_bot.repeat is False  # default


def test_dns_client_install():
    """Test that the DNS Client service can be configured via config."""
    game = load_config(BASIC_CONFIG)
    client_1: Computer = game.simulation.network.get_node_by_hostname("client_1")

    dns_client: DNSClient = client_1.software_manager.software.get("DNSClient")

    assert dns_client.dns_server == IPv4Address("192.168.1.10")


def test_dns_server_install():
    """Test that the DNS Client service can be configured via config."""
    game = load_config(BASIC_CONFIG)
    client_1: Computer = game.simulation.network.get_node_by_hostname("client_1")

    dns_server: DNSServer = client_1.software_manager.software.get("DNSServer")

    assert dns_server.dns_lookup("arcd.com") == IPv4Address("192.168.1.10")


def test_database_service_install():
    """Test that the Database Service can be configured via config."""
    game = load_config(BASIC_CONFIG)
    client_1: Computer = game.simulation.network.get_node_by_hostname("client_1")

    database_service: DatabaseService = client_1.software_manager.software.get("DatabaseService")

    assert database_service.backup_server_ip == IPv4Address("192.168.1.10")


def test_web_server_install():
    """Test that the Web Server Service can be configured via config."""
    game = load_config(BASIC_CONFIG)
    client_1: Computer = game.simulation.network.get_node_by_hostname("client_1")

    web_server_service: WebServer = client_1.software_manager.software.get("WebServer")

    # config should have also installed database client - web server service should be able to retrieve this
    assert web_server_service.software_manager.software.get("DatabaseClient") is not None


def test_ftp_client_install():
    """Test that the FTP Client Service can be configured via config."""
    game = load_config(BASIC_CONFIG)
    client_1: Computer = game.simulation.network.get_node_by_hostname("client_1")

    ftp_client_service: FTPClient = client_1.software_manager.software.get("FTPClient")
    assert ftp_client_service is not None


def test_ftp_server_install():
    """Test that the FTP Server Service can be configured via config."""
    game = load_config(BASIC_CONFIG)
    client_1: Computer = game.simulation.network.get_node_by_hostname("client_1")

    ftp_server_service: FTPServer = client_1.software_manager.software.get("FTPServer")
    assert ftp_server_service is not None
    assert ftp_server_service.server_password == "arcd"


def test_ntp_client_install():
    """Test that the NTP Client Service can be configured via config."""
    game = load_config(BASIC_CONFIG)
    client_1: Computer = game.simulation.network.get_node_by_hostname("client_1")

    ntp_client_service: NTPClient = client_1.software_manager.software.get("NTPClient")
    assert ntp_client_service is not None
    assert ntp_client_service.ntp_server == IPv4Address("192.168.1.10")


def test_ntp_server_install():
    """Test that the NTP Server Service can be configured via config."""
    game = load_config(BASIC_CONFIG)
    client_1: Computer = game.simulation.network.get_node_by_hostname("client_1")

    ntp_server_service: NTPServer = client_1.software_manager.software.get("NTPServer")
    assert ntp_server_service is not None
