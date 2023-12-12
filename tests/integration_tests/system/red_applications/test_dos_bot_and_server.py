from ipaddress import IPv4Address
from typing import Tuple

import pytest

from primaite.simulator.network.hardware.nodes.computer import Computer
from primaite.simulator.network.hardware.nodes.server import Server
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.application import ApplicationOperatingState
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
        target_ip_address=IPv4Address(server.nics.get(next(iter(server.nics))).ip_address),
        target_port=Port.POSTGRES_SERVER,
    )

    # Install FTP Server service on server
    server.software_manager.install(DatabaseService)
    db_server_service: DatabaseService = server.software_manager.software.get("DatabaseService")
    db_server_service.start()

    return dos_bot, computer, db_server_service, server


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
    db_server_service.health_state_actual = SoftwareHealthState.GOOD
    assert len(db_server_service.connections) == 0

    computer.apply_timestep(timestep=1)
    server.apply_timestep(timestep=1)

    assert len(dos_bot.connections) == db_server_service.max_sessions
    assert len(db_server_service.connections) == db_server_service.max_sessions
    assert len(dos_bot.connections) == db_server_service.max_sessions

    assert dos_bot.attack_stage is DoSAttackStage.NOT_STARTED
    assert db_server_service.health_state_actual is SoftwareHealthState.OVERWHELMED


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
    db_server_service.health_state_actual = SoftwareHealthState.GOOD
    assert len(db_server_service.connections) == 0

    computer.apply_timestep(timestep=1)
    server.apply_timestep(timestep=1)

    assert len(dos_bot.connections) == 0
    assert len(db_server_service.connections) == 0
    assert len(dos_bot.connections) == 0

    assert dos_bot.attack_stage is DoSAttackStage.COMPLETED
    assert db_server_service.health_state_actual is SoftwareHealthState.GOOD


def test_dos_bot_database_service_connection(dos_bot_and_db_server):
    dos_bot, computer, db_server_service, server = dos_bot_and_db_server

    dos_bot.operating_state = ApplicationOperatingState.RUNNING
    dos_bot.attack_stage = DoSAttackStage.PORT_SCAN
    dos_bot._perform_dos()

    assert len(dos_bot.connections) == db_server_service.max_sessions
    assert len(db_server_service.connections) == db_server_service.max_sessions
    assert len(dos_bot.connections) == db_server_service.max_sessions
