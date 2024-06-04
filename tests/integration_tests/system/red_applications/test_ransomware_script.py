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
from primaite.simulator.system.applications.red_applications.ransomware_script import (
    RansomwareAttackStage,
    RansomwareScript,
)
from primaite.simulator.system.services.database.database_service import DatabaseService
from primaite.simulator.system.software import SoftwareHealthState


@pytest.fixture(scope="function")
def ransomware_script_and_db_server(client_server) -> Tuple[RansomwareScript, Computer, DatabaseService, Server]:
    computer, server = client_server

    # install db client on computer
    computer.software_manager.install(DatabaseClient)
    db_client: DatabaseClient = computer.software_manager.software.get("DatabaseClient")
    db_client.run()

    # Install DoSBot on computer
    computer.software_manager.install(RansomwareScript)

    ransomware_script_application: RansomwareScript = computer.software_manager.software.get("RansomwareScript")
    ransomware_script_application.configure(
        server_ip_address=IPv4Address(server.network_interface[1].ip_address), payload="ENCRYPT"
    )

    # Install DB Server service on server
    server.software_manager.install(DatabaseService)
    db_server_service: DatabaseService = server.software_manager.software.get("DatabaseService")
    db_server_service.start()

    return ransomware_script_application, computer, db_server_service, server


@pytest.fixture(scope="function")
def ransomware_script_db_server_green_client(example_network) -> Network:
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

    # install Ransomware Script bot on client 1
    client_1.software_manager.install(RansomwareScript)

    ransomware_script_application: RansomwareScript = client_1.software_manager.software.get("RansomwareScript")
    ransomware_script_application.configure(
        server_ip_address=IPv4Address(server.network_interface[1].ip_address), payload="ENCRYPT"
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


def test_repeating_ransomware_script_attack(ransomware_script_and_db_server):
    """Test a repeating data manipulation attack."""
    RansomwareScript, computer, db_server_service, server = ransomware_script_and_db_server

    assert db_server_service.health_state_actual is SoftwareHealthState.GOOD
    assert computer.file_system.num_file_creations == 0

    RansomwareScript.target_scan_p_of_success = 1
    RansomwareScript.c2_beacon_p_of_success = 1
    RansomwareScript.ransomware_encrypt_p_of_success = 1
    RansomwareScript.repeat = True
    RansomwareScript.attack()

    assert RansomwareScript.attack_stage == RansomwareAttackStage.NOT_STARTED
    assert db_server_service.db_file.health_status is FileSystemItemHealthStatus.COMPROMISED
    assert computer.file_system.num_file_creations == 1

    computer.apply_timestep(timestep=1)
    server.apply_timestep(timestep=1)

    assert RansomwareScript.attack_stage == RansomwareAttackStage.NOT_STARTED
    assert db_server_service.db_file.health_status is FileSystemItemHealthStatus.COMPROMISED


def test_repeating_ransomware_script_attack(ransomware_script_and_db_server):
    """Test a repeating ransowmare script attack."""
    RansomwareScript, computer, db_server_service, server = ransomware_script_and_db_server

    assert db_server_service.health_state_actual is SoftwareHealthState.GOOD

    RansomwareScript.target_scan_p_of_success = 1
    RansomwareScript.c2_beacon_p_of_success = 1
    RansomwareScript.ransomware_encrypt_p_of_success = 1
    RansomwareScript.repeat = False
    RansomwareScript.attack()

    assert RansomwareScript.attack_stage == RansomwareAttackStage.SUCCEEDED
    assert db_server_service.db_file.health_status is FileSystemItemHealthStatus.CORRUPT

    computer.apply_timestep(timestep=1)
    computer.pre_timestep(timestep=1)
    server.apply_timestep(timestep=1)
    server.pre_timestep(timestep=1)

    assert RansomwareScript.attack_stage == RansomwareAttackStage.SUCCEEDED
    assert db_server_service.db_file.health_status is FileSystemItemHealthStatus.CORRUPT
    assert computer.file_system.num_file_creations == 0


def test_ransomware_disrupts_green_agent_connection(ransomware_script_db_server_green_client):
    """Test to see show that the database service still operate"""
    network: Network = ransomware_script_db_server_green_client

    client_1: Computer = network.get_node_by_hostname("client_1")
    ransomware_script_application: RansomwareScript = client_1.software_manager.software.get("RansomwareScript")

    client_2: Computer = network.get_node_by_hostname("client_2")
    green_db_client: DatabaseClient = client_2.software_manager.software.get("DatabaseClient")
    green_db_client_connection: DatabaseClientConnection = green_db_client.get_new_connection()

    server: Server = network.get_node_by_hostname("server_1")
    db_server_service: DatabaseService = server.software_manager.software.get("DatabaseService")

    assert db_server_service.db_file.health_status is FileSystemItemHealthStatus.GOOD
    assert green_db_client_connection.query("SELECT")
    assert green_db_client.last_query_response.get("status_code") == 200

    ransomware_script_application.target_scan_p_of_success = 1
    ransomware_script_application.ransomware_encrypt_p_of_success = 1
    ransomware_script_application.c2_beacon_p_of_success = 1
    ransomware_script_application.repeat = False
    ransomware_script_application.attack()

    assert db_server_service.db_file.health_status is FileSystemItemHealthStatus.CORRUPT
    assert green_db_client_connection.query("SELECT") is True
    assert green_db_client.last_query_response.get("status_code") == 200
