from ipaddress import IPv4Address
from typing import Tuple

import pytest

from primaite.simulator.file_system.file_system_item_abc import FileSystemItemHealthStatus
from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.hardware.nodes.network.router import ACLAction, Router
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.application import ApplicationOperatingState
from primaite.simulator.system.applications.database_client import DatabaseClient, DatabaseClientConnection
from primaite.simulator.system.applications.red_applications.data_manipulation_bot import (
    DataManipulationAttackStage,
    DataManipulationBot,
)
from primaite.simulator.system.applications.red_applications.dos_bot import DoSAttackStage, DoSBot
from primaite.simulator.system.services.database.database_service import DatabaseService
from primaite.simulator.system.software import SoftwareHealthState


@pytest.fixture(scope="function")
def data_manipulation_bot_and_db_server(client_server) -> Tuple[DataManipulationBot, Computer, DatabaseService, Server]:
    computer, server = client_server

    # install db client on computer
    computer.software_manager.install(DatabaseClient)
    db_client: DatabaseClient = computer.software_manager.software.get("DatabaseClient")
    db_client.run()

    # Install DoSBot on computer
    computer.software_manager.install(DataManipulationBot)

    data_manipulation_bot: DataManipulationBot = computer.software_manager.software.get("DataManipulationBot")
    data_manipulation_bot.configure(
        server_ip_address=IPv4Address(server.network_interface[1].ip_address), payload="DELETE"
    )

    # Install DB Server service on server
    server.software_manager.install(DatabaseService)
    db_server_service: DatabaseService = server.software_manager.software.get("DatabaseService")
    db_server_service.start()

    return data_manipulation_bot, computer, db_server_service, server


@pytest.fixture(scope="function")
def data_manipulation_db_server_green_client(example_network) -> Network:
    network: Network = example_network

    router_1: Router = example_network.get_node_by_hostname("router_1")
    router_1.acl.add_rule(
        action=ACLAction.PERMIT, src_port=Port.POSTGRES_SERVER, dst_port=Port.POSTGRES_SERVER, position=0
    )

    client_1: Computer = network.get_node_by_hostname("client_1")
    client_2: Computer = network.get_node_by_hostname("client_2")
    server: Server = network.get_node_by_hostname("server_1")

    # install db client on client 1
    client_1.software_manager.install(DatabaseClient)
    db_client: DatabaseClient = client_1.software_manager.software.get("DatabaseClient")
    db_client.run()

    # install Data Manipulation bot on client 1
    client_1.software_manager.install(DataManipulationBot)

    data_manipulation_bot: DataManipulationBot = client_1.software_manager.software.get("DataManipulationBot")
    data_manipulation_bot.configure(
        server_ip_address=IPv4Address(server.network_interface[1].ip_address), payload="DELETE"
    )

    # install db server service on server
    server.software_manager.install(DatabaseService)
    db_server_service: DatabaseService = server.software_manager.software.get("DatabaseService")
    db_server_service.start()

    # Install DB client (green) on client 2
    client_2.software_manager.install(DatabaseClient)

    database_client: DatabaseClient = client_2.software_manager.software.get("DatabaseClient")
    database_client.configure(server_ip_address=IPv4Address(server.network_interface[1].ip_address))
    database_client.run()

    return network


def test_repeating_data_manipulation_attack(data_manipulation_bot_and_db_server):
    """Test a repeating data manipulation attack."""
    data_manipulation_bot, computer, db_server_service, server = data_manipulation_bot_and_db_server

    assert db_server_service.health_state_actual is SoftwareHealthState.GOOD

    data_manipulation_bot.port_scan_p_of_success = 1
    data_manipulation_bot.data_manipulation_p_of_success = 1
    data_manipulation_bot.repeat = True
    data_manipulation_bot.attack()

    assert data_manipulation_bot.attack_stage == DataManipulationAttackStage.NOT_STARTED
    assert db_server_service.db_file.health_status is FileSystemItemHealthStatus.COMPROMISED

    computer.apply_timestep(timestep=1)
    server.apply_timestep(timestep=1)

    assert data_manipulation_bot.attack_stage == DataManipulationAttackStage.NOT_STARTED
    assert db_server_service.db_file.health_status is FileSystemItemHealthStatus.COMPROMISED


def test_non_repeating_data_manipulation_attack(data_manipulation_bot_and_db_server):
    """Test a non repeating data manipulation attack."""
    data_manipulation_bot, computer, db_server_service, server = data_manipulation_bot_and_db_server

    assert db_server_service.health_state_actual is SoftwareHealthState.GOOD

    data_manipulation_bot.port_scan_p_of_success = 1
    data_manipulation_bot.data_manipulation_p_of_success = 1
    data_manipulation_bot.repeat = False
    data_manipulation_bot.attack()

    assert data_manipulation_bot.attack_stage == DataManipulationAttackStage.SUCCEEDED
    assert db_server_service.db_file.health_status is FileSystemItemHealthStatus.COMPROMISED

    computer.apply_timestep(timestep=1)
    server.apply_timestep(timestep=1)

    assert data_manipulation_bot.attack_stage == DataManipulationAttackStage.SUCCEEDED
    assert db_server_service.db_file.health_status is FileSystemItemHealthStatus.COMPROMISED


def test_data_manipulation_disrupts_green_agent_connection(data_manipulation_db_server_green_client):
    """Test to see that the data manipulation bot affects a green agent query."""
    network: Network = data_manipulation_db_server_green_client

    client_1: Computer = network.get_node_by_hostname("client_1")
    data_manipulation_bot: DataManipulationBot = client_1.software_manager.software.get("DataManipulationBot")

    client_2: Computer = network.get_node_by_hostname("client_2")
    green_db_client: DatabaseClient = client_2.software_manager.software.get("DatabaseClient")

    server: Server = network.get_node_by_hostname("server_1")
    db_server_service: DatabaseService = server.software_manager.software.get("DatabaseService")

    green_db_connection: DatabaseClientConnection = green_db_client.get_new_connection()

    assert db_server_service.db_file.health_status is FileSystemItemHealthStatus.GOOD
    assert green_db_connection.query("SELECT")
    assert green_db_client.last_query_response.get("status_code") == 200

    data_manipulation_bot.port_scan_p_of_success = 1
    data_manipulation_bot.data_manipulation_p_of_success = 1
    data_manipulation_bot.repeat = False
    data_manipulation_bot.attack()

    assert db_server_service.db_file.health_status is FileSystemItemHealthStatus.COMPROMISED
    assert green_db_connection.query("SELECT") is False
    assert green_db_client.last_query_response.get("status_code") != 200
