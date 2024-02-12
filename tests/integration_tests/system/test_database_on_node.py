from ipaddress import IPv4Address
from typing import Tuple

import pytest

from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.services.database.database_service import DatabaseService
from primaite.simulator.system.services.ftp.ftp_server import FTPServer
from primaite.simulator.system.services.service import ServiceOperatingState


@pytest.fixture(scope="function")
def peer_to_peer() -> Tuple[Computer, Computer]:
    network = Network()
    node_a = Computer(hostname="node_a", ip_address="192.168.0.10", subnet_mask="255.255.255.0", start_up_duration=0)
    node_a.power_on()
    node_a.software_manager.get_open_ports()

    node_b = Computer(hostname="node_b", ip_address="192.168.0.11", subnet_mask="255.255.255.0", start_up_duration=0)
    node_b.power_on()
    network.connect(node_a.network_interface[1], node_b.network_interface[1])

    assert node_a.ping("192.168.0.11")

    node_a.software_manager.install(DatabaseClient)
    node_a.software_manager.software["DatabaseClient"].configure(server_ip_address=IPv4Address("192.168.0.11"))
    node_a.software_manager.software["DatabaseClient"].run()

    node_b.software_manager.install(DatabaseService)
    database_service: DatabaseService = node_b.software_manager.software["DatabaseService"]  # noqa
    database_service.start()
    return node_a, node_b


@pytest.fixture(scope="function")
def peer_to_peer_secure_db(peer_to_peer) -> Tuple[Computer, Computer]:
    node_a, node_b = peer_to_peer

    database_service: DatabaseService = node_b.software_manager.software["DatabaseService"]  # noqa
    database_service.stop()
    database_service.password = "12345"
    database_service.start()
    return node_a, node_b


def test_database_client_server_connection(peer_to_peer):
    node_a, node_b = peer_to_peer

    db_client: DatabaseClient = node_a.software_manager.software["DatabaseClient"]

    db_service: DatabaseService = node_b.software_manager.software["DatabaseService"]

    db_client.connect()
    assert len(db_client.connections) == 1
    assert len(db_service.connections) == 1

    db_client.disconnect()
    assert len(db_client.connections) == 0
    assert len(db_service.connections) == 0


def test_database_client_server_correct_password(peer_to_peer_secure_db):
    node_a, node_b = peer_to_peer_secure_db

    db_client: DatabaseClient = node_a.software_manager.software["DatabaseClient"]

    db_service: DatabaseService = node_b.software_manager.software["DatabaseService"]

    db_client.configure(server_ip_address=IPv4Address("192.168.0.11"), server_password="12345")
    db_client.connect()
    assert len(db_client.connections) == 1
    assert len(db_service.connections) == 1


def test_database_client_server_incorrect_password(peer_to_peer_secure_db):
    node_a, node_b = peer_to_peer_secure_db

    db_client: DatabaseClient = node_a.software_manager.software["DatabaseClient"]

    db_service: DatabaseService = node_b.software_manager.software["DatabaseService"]

    # should fail
    db_client.connect()
    assert len(db_client.connections) == 0
    assert len(db_service.connections) == 0

    db_client.configure(server_ip_address=IPv4Address("192.168.0.11"), server_password="wrongpass")
    db_client.connect()
    assert len(db_client.connections) == 0
    assert len(db_service.connections) == 0


def test_database_client_query(uc2_network):
    """Tests DB query across the network returns HTTP status 200 and date."""
    web_server: Server = uc2_network.get_node_by_hostname("web_server")
    db_client: DatabaseClient = web_server.software_manager.software["DatabaseClient"]
    db_client.connect()

    assert db_client.query("SELECT")


def test_create_database_backup(uc2_network):
    """Run the backup_database method and check if the FTP server has the relevant file."""
    db_server: Server = uc2_network.get_node_by_hostname("database_server")
    db_service: DatabaseService = db_server.software_manager.software["DatabaseService"]

    # back up should be created
    assert db_service.backup_database() is True

    backup_server: Server = uc2_network.get_node_by_hostname("backup_server")
    ftp_server: FTPServer = backup_server.software_manager.software["FTPServer"]

    # backup file should exist in the backup server
    assert ftp_server.file_system.get_file(folder_name=db_service.uuid, file_name="database.db") is not None


def test_restore_backup(uc2_network):
    """Run the restore_backup method and check if the backup is properly restored."""
    db_server: Server = uc2_network.get_node_by_hostname("database_server")
    db_service: DatabaseService = db_server.software_manager.software["DatabaseService"]

    # create a back up
    assert db_service.backup_database() is True

    # delete database locally
    db_service.file_system.delete_file(folder_name="database", file_name="database.db")

    assert db_service.file_system.get_file(folder_name="database", file_name="database.db") is None

    # back up should be restored
    assert db_service.restore_backup() is True

    assert db_service.file_system.get_file(folder_name="database", file_name="database.db") is not None


def test_database_client_cannot_query_offline_database_server(uc2_network):
    """Tests DB query across the network returns HTTP status 404 when db server is offline."""
    db_server: Server = uc2_network.get_node_by_hostname("database_server")
    db_service: DatabaseService = db_server.software_manager.software.get("DatabaseService")

    assert db_server.operating_state is NodeOperatingState.ON
    assert db_service.operating_state is ServiceOperatingState.RUNNING

    web_server: Server = uc2_network.get_node_by_hostname("web_server")
    db_client: DatabaseClient = web_server.software_manager.software.get("DatabaseClient")
    assert len(db_client.connections)

    assert db_client.query("SELECT") is True

    db_server.power_off()

    for i in range(db_server.shut_down_duration + 1):
        uc2_network.apply_timestep(timestep=i)

    assert db_server.operating_state is NodeOperatingState.OFF
    assert db_service.operating_state is ServiceOperatingState.STOPPED

    assert db_client.query("SELECT") is False
