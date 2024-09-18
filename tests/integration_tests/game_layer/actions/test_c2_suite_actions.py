# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from ipaddress import IPv4Address
from typing import Tuple

import pytest

from primaite.game.agent.interface import ProxyAgent
from primaite.game.game import PrimaiteGame
from primaite.simulator.file_system.file_system_item_abc import FileSystemItemHealthStatus
from primaite.simulator.network.hardware.base import UserManager
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.hardware.nodes.network.router import ACLAction
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.red_applications.c2.c2_beacon import C2Beacon
from primaite.simulator.system.applications.red_applications.c2.c2_server import C2Command, C2Server
from primaite.simulator.system.services.database.database_service import DatabaseService
from primaite.simulator.system.services.ftp.ftp_client import FTPClient
from primaite.simulator.system.services.ftp.ftp_server import FTPServer
from primaite.simulator.system.services.service import ServiceOperatingState


@pytest.fixture
def game_and_agent_fixture(game_and_agent):
    """Create a game with a simple agent that can be controlled by the tests."""
    game, agent = game_and_agent

    router = game.simulation.network.get_node_by_hostname("router")
    router.acl.add_rule(action=ACLAction.PERMIT, src_port=Port["HTTP"], dst_port=Port["HTTP"], position=4)
    router.acl.add_rule(action=ACLAction.PERMIT, src_port=Port["DNS"], dst_port=Port["DNS"], position=5)
    router.acl.add_rule(action=ACLAction.PERMIT, src_port=Port["FTP"], dst_port=Port["FTP"], position=6)

    c2_server_host = game.simulation.network.get_node_by_hostname("client_1")
    c2_server_host.software_manager.install(software_class=C2Server)
    c2_server: C2Server = c2_server_host.software_manager.software["C2Server"]
    c2_server.run()

    return (game, agent)


def test_c2_beacon_default(game_and_agent_fixture: Tuple[PrimaiteGame, ProxyAgent]):
    """Tests that a Red Agent can install, configure and establish a C2 Beacon (default params)."""
    game, agent = game_and_agent_fixture

    # Installing C2 Beacon on Server_1
    server_1: Server = game.simulation.network.get_node_by_hostname("server_1")

    action = (
        "NODE_APPLICATION_INSTALL",
        {"node_id": 1, "application_name": "C2Beacon"},
    )
    agent.store_action(action)
    game.step()
    assert agent.history[-1].response.status == "success"

    action = (
        "CONFIGURE_C2_BEACON",
        {
            "node_id": 1,
            "config": {
                "c2_server_ip_address": "10.0.1.2",
                "keep_alive_frequency": 5,
                "masquerade_protocol": "TCP",
                "masquerade_port": "HTTP",
            },
        },
    )
    agent.store_action(action)
    game.step()
    assert agent.history[-1].response.status == "success"

    action = (
        "NODE_APPLICATION_EXECUTE",
        {"node_id": 1, "application_id": 0},
    )
    agent.store_action(action)
    game.step()
    assert agent.history[-1].response.status == "success"

    # Asserting that we've confirmed our connection
    c2_beacon: C2Beacon = server_1.software_manager.software["C2Beacon"]
    assert c2_beacon.c2_connection_active == True


def test_c2_server_ransomware(game_and_agent_fixture: Tuple[PrimaiteGame, ProxyAgent]):
    """Tests that a Red Agent can install a RansomwareScript, Configure and launch all via C2 Server actions."""
    game, agent = game_and_agent_fixture

    # Installing a C2 Beacon on server_1
    server_1: Server = game.simulation.network.get_node_by_hostname("server_1")
    server_1.software_manager.install(C2Beacon)

    # Installing a database on Server_2 for the ransomware to attack
    server_2: Server = game.simulation.network.get_node_by_hostname("server_2")
    server_2.software_manager.install(DatabaseService)
    server_2.software_manager.software["DatabaseService"].start()
    # Configuring the C2 to connect to client 1 (C2 Server)
    c2_beacon: C2Beacon = server_1.software_manager.software["C2Beacon"]
    c2_beacon.configure(c2_server_ip_address=IPv4Address("10.0.1.2"))
    c2_beacon.establish()
    assert c2_beacon.c2_connection_active == True

    # C2 Action 1: Installing the RansomwareScript & Database client via Terminal

    action = (
        "C2_SERVER_TERMINAL_COMMAND",
        {
            "node_id": 0,
            "ip_address": None,
            "account": {
                "username": "admin",
                "password": "admin",
            },
            "commands": [
                ["software_manager", "application", "install", "RansomwareScript"],
                ["software_manager", "application", "install", "DatabaseClient"],
            ],
        },
    )
    agent.store_action(action)
    game.step()
    assert agent.history[-1].response.status == "success"

    action = (
        "C2_SERVER_RANSOMWARE_CONFIGURE",
        {
            "node_id": 0,
            "config": {"server_ip_address": "10.0.2.3", "payload": "ENCRYPT"},
        },
    )
    agent.store_action(action)
    game.step()
    assert agent.history[-1].response.status == "success"

    # Stepping a few timesteps to allow for the RansowmareScript to finish installing.

    action = ("DONOTHING", {})
    agent.store_action(action)
    game.step()
    game.step()
    game.step()

    action = (
        "C2_SERVER_RANSOMWARE_LAUNCH",
        {
            "node_id": 0,
        },
    )
    agent.store_action(action)
    game.step()
    assert agent.history[-1].response.status == "success"

    database_file = server_2.software_manager.file_system.get_file("database", "database.db")
    assert database_file.health_status == FileSystemItemHealthStatus.CORRUPT


def test_c2_server_data_exfiltration(game_and_agent_fixture: Tuple[PrimaiteGame, ProxyAgent]):
    """Tests that a Red Agent can extract a database.db file via C2 Server actions."""
    game, agent = game_and_agent_fixture

    # Installing a C2 Beacon on server_1
    server_1: Server = game.simulation.network.get_node_by_hostname("server_1")
    server_1.software_manager.install(C2Beacon)

    # Installing a database on Server_2 (creates a database.db file.)
    server_2: Server = game.simulation.network.get_node_by_hostname("server_2")
    server_2.software_manager.install(DatabaseService)
    server_2.software_manager.software["DatabaseService"].start()

    # Configuring the C2 to connect to client 1 (C2 Server)
    c2_beacon: C2Beacon = server_1.software_manager.software["C2Beacon"]
    c2_beacon.configure(c2_server_ip_address=IPv4Address("10.0.1.2"))
    c2_beacon.establish()
    assert c2_beacon.c2_connection_active == True

    # Selecting a target file to steal: database.db
    # Server 2 ip : 10.0.2.3
    database_file = server_2.software_manager.file_system.get_file(folder_name="database", file_name="database.db")
    assert database_file is not None

    # C2 Action: Data exfiltrate.

    action = (
        "C2_SERVER_DATA_EXFILTRATE",
        {
            "node_id": 0,
            "target_file_name": "database.db",
            "target_folder_name": "database",
            "exfiltration_folder_name": "spoils",
            "target_ip_address": "10.0.2.3",
            "account": {
                "username": "admin",
                "password": "admin",
            },
        },
    )
    agent.store_action(action)
    game.step()

    assert server_1.file_system.access_file(folder_name="spoils", file_name="database.db")

    client_1 = game.simulation.network.get_node_by_hostname("client_1")
    assert client_1.file_system.access_file(folder_name="spoils", file_name="database.db")
