# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from ipaddress import IPv4Address
from typing import Tuple

import pytest

from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.hardware.nodes.network.router import ACLAction, Router
from primaite.simulator.network.transmission.transport_layer import PORT_LOOKUP
from primaite.simulator.system.applications.application import ApplicationOperatingState
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.applications.red_applications.dos_bot import DoSAttackStage, DoSBot
from primaite.simulator.system.services.database.database_service import DatabaseService
from primaite.simulator.system.software import SoftwareHealthState


@pytest.fixture(scope="function")
def dos_bot_and_db_server(client_server) -> Tuple[DoSBot, Computer, DatabaseService, Server]:
    computer, server = client_server

    # Install DoSBot on computer
    computer.software_manager.install(DoSBot)

    dos_bot: DoSBot = computer.software_manager.software.get("DoSBot")
    dos_bot.configure(
        target_ip_address=IPv4Address(server.network_interface[1].ip_address),
        target_port=PORT_LOOKUP["POSTGRES_SERVER"],
    )

    # Install DB Server service on server
    server.software_manager.install(DatabaseService)
    db_server_service: DatabaseService = server.software_manager.software.get("DatabaseService")
    db_server_service.start()

    return dos_bot, computer, db_server_service, server


@pytest.fixture(scope="function")
def dos_bot_db_server_green_client(example_network) -> Network:
    network: Network = example_network

    router_1: Router = example_network.get_node_by_hostname("router_1")
    router_1.acl.add_rule(
        action=ACLAction.PERMIT,
        src_port=PORT_LOOKUP["POSTGRES_SERVER"],
        dst_port=PORT_LOOKUP["POSTGRES_SERVER"],
        position=0,
    )

    client_1: Computer = network.get_node_by_hostname("client_1")
    client_2: Computer = network.get_node_by_hostname("client_2")
    server: Server = network.get_node_by_hostname("server_1")

    # install DoS bot on client 1
    client_1.software_manager.install(DoSBot)

    dos_bot: DoSBot = client_1.software_manager.software.get("DoSBot")
    dos_bot.configure(
        target_ip_address=IPv4Address(server.network_interface[1].ip_address),
        target_port=PORT_LOOKUP["POSTGRES_SERVER"],
    )

    # install db server service on server
    server.software_manager.install(DatabaseService)
    db_server_service: DatabaseService = server.software_manager.software.get("DatabaseService")
    db_server_service.start()

    # Install DB client (green) on client 2
    client_2.software_manager.install(DatabaseClient)

    database_client: DatabaseClient = client_2.software_manager.software.get("DatabaseClient")
    database_client.configure(server_ip_address=IPv4Address("192.168.0.1"))
    database_client.run()

    return network


@pytest.mark.xfail(reason="Tests fail due to recent changes in how DB connections are handled for example layout.")
def test_repeating_dos_attack(dos_bot_and_db_server):
    dos_bot, computer, db_server_service, server = dos_bot_and_db_server

    assert db_server_service.health_state_actual is SoftwareHealthState.GOOD

    dos_bot.port_scan_p_of_success = 1
    dos_bot.repeat = True
    dos_bot.run()

    assert len(dos_bot.connections) == db_server_service.max_sessions
    assert len(db_server_service.connections) == db_server_service.max_sessions
    assert len(dos_bot.connections) == db_server_service.max_sessions

    assert dos_bot.attack_stage is DoSAttackStage.NOT_STARTED
    assert db_server_service.health_state_actual is SoftwareHealthState.OVERWHELMED

    db_server_service.clear_connections()
    db_server_service.set_health_state(SoftwareHealthState.GOOD)
    assert len(db_server_service.connections) == 0

    computer.apply_timestep(timestep=1)
    server.apply_timestep(timestep=1)

    assert len(dos_bot.connections) == db_server_service.max_sessions
    assert len(db_server_service.connections) == db_server_service.max_sessions
    assert len(dos_bot.connections) == db_server_service.max_sessions

    assert dos_bot.attack_stage is DoSAttackStage.NOT_STARTED
    assert db_server_service.health_state_actual is SoftwareHealthState.OVERWHELMED


@pytest.mark.xfail(reason="Tests fail due to recent changes in how DB connections are handled for example layout.")
def test_non_repeating_dos_attack(dos_bot_and_db_server):
    dos_bot, computer, db_server_service, server = dos_bot_and_db_server

    assert db_server_service.health_state_actual is SoftwareHealthState.GOOD

    dos_bot.port_scan_p_of_success = 1
    dos_bot.repeat = False
    dos_bot.run()

    assert len(dos_bot.connections) == db_server_service.max_sessions
    assert len(db_server_service.connections) == db_server_service.max_sessions
    assert len(dos_bot.connections) == db_server_service.max_sessions

    assert dos_bot.attack_stage is DoSAttackStage.COMPLETED
    assert db_server_service.health_state_actual is SoftwareHealthState.OVERWHELMED

    db_server_service.clear_connections()
    db_server_service.set_health_state(SoftwareHealthState.GOOD)
    assert len(db_server_service.connections) == 0

    computer.apply_timestep(timestep=1)
    server.apply_timestep(timestep=1)

    assert len(dos_bot.connections) == 0
    assert len(db_server_service.connections) == 0
    assert len(dos_bot.connections) == 0

    assert dos_bot.attack_stage is DoSAttackStage.COMPLETED
    assert db_server_service.health_state_actual is SoftwareHealthState.GOOD


@pytest.mark.xfail(reason="Tests fail due to recent changes in how DB connections are handled for example layout.")
def test_dos_bot_database_service_connection(dos_bot_and_db_server):
    dos_bot, computer, db_server_service, server = dos_bot_and_db_server

    dos_bot.operating_state = ApplicationOperatingState.RUNNING
    dos_bot.attack_stage = DoSAttackStage.PORT_SCAN
    dos_bot._perform_dos()

    assert len(dos_bot.connections) == db_server_service.max_sessions
    assert len(db_server_service.connections) == db_server_service.max_sessions
    assert len(dos_bot.connections) == db_server_service.max_sessions


@pytest.mark.xfail(reason="Tests fail due to recent changes in how DB connections are handled for example layout.")
def test_dos_blocks_green_agent_connection(dos_bot_db_server_green_client):
    network: Network = dos_bot_db_server_green_client

    client_1: Computer = network.get_node_by_hostname("client_1")
    dos_bot: DoSBot = client_1.software_manager.software.get("DoSBot")

    client_2: Computer = network.get_node_by_hostname("client_2")
    green_db_client: DatabaseClient = client_2.software_manager.software.get("DatabaseClient")

    server: Server = network.get_node_by_hostname("server_1")
    db_server_service: DatabaseService = server.software_manager.software.get("DatabaseService")

    assert db_server_service.health_state_actual is SoftwareHealthState.GOOD

    dos_bot.port_scan_p_of_success = 1
    dos_bot.repeat = False
    dos_bot.run()

    # DoS bot fills up connection of db server service
    assert len(dos_bot.connections) == db_server_service.max_sessions
    assert len(db_server_service.connections) == db_server_service.max_sessions
    assert len(dos_bot.connections) == db_server_service.max_sessions
    assert len(green_db_client.connections) == 0

    assert dos_bot.attack_stage is DoSAttackStage.COMPLETED
    # db server service is overwhelmed
    assert db_server_service.health_state_actual is SoftwareHealthState.OVERWHELMED

    # green agent tries to connect but fails because service is overwhelmed
    assert green_db_client.connect() is False
    assert len(green_db_client.connections) == 0
