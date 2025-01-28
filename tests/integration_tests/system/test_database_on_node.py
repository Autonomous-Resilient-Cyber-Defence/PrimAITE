# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from ipaddress import IPv4Address
from typing import Tuple

import pytest

from primaite.simulator.file_system.file_system_item_abc import FileSystemItemHealthStatus
from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.hardware.nodes.network.switch import Switch
from primaite.simulator.system.applications.database_client import DatabaseClient, DatabaseClientConnection
from primaite.simulator.system.services.database.database_service import DatabaseService
from primaite.simulator.system.services.ftp.ftp_server import FTPServer
from primaite.simulator.system.services.service import ServiceOperatingState
from primaite.simulator.system.software import SoftwareHealthState


@pytest.fixture(scope="function")
def peer_to_peer() -> Tuple[Computer, Computer]:
    network = Network()
    node_a: Computer = Computer.from_config(config={"type":"computer", "hostname":"node_a", "ip_address":"192.168.0.10", "subnet_mask":"255.255.255.0", "start_up_duration":0})
    node_a.power_on()
    node_a.software_manager.get_open_ports()

    node_b: Computer = Computer.from_config(config={"type":"computer", "hostname":"node_b", "ip_address":"192.168.0.11", "subnet_mask":"255.255.255.0", "start_up_duration":0})
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

    assert len(db_client.client_connections) == 1
    assert len(db_service.connections) == 1

    db_client.disconnect()
    assert len(db_client.client_connections) == 0
    assert len(db_service.connections) == 0


def test_database_client_server_correct_password(peer_to_peer_secure_db):
    node_a, node_b = peer_to_peer_secure_db

    db_client: DatabaseClient = node_a.software_manager.software["DatabaseClient"]

    db_service: DatabaseService = node_b.software_manager.software["DatabaseService"]

    db_client.configure(server_ip_address=IPv4Address("192.168.0.11"), server_password="12345")
    db_client.connect()
    assert len(db_client.client_connections) == 1
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


def test_database_client_native_connection_query(uc2_network):
    """Tests DB query across the network returns HTTP status 200 and date."""
    web_server: Server = uc2_network.get_node_by_hostname("web_server")
    db_client: DatabaseClient = web_server.software_manager.software["DatabaseClient"]
    db_client.connect()
    assert db_client.query(sql="SELECT")
    assert db_client.query(sql="INSERT")


def test_database_client_connection_query(uc2_network):
    """Tests DB query across the network returns HTTP status 200 and date."""
    web_server: Server = uc2_network.get_node_by_hostname("web_server")
    db_client: DatabaseClient = web_server.software_manager.software["DatabaseClient"]

    db_connection: DatabaseClientConnection = db_client.get_new_connection()

    assert db_connection.query(sql="SELECT")
    assert db_connection.query(sql="INSERT")


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


def test_restore_backup_without_updating_scan(uc2_network):
    """Same test as restore backup but the file is previously seen as corrupted."""
    db_server: Server = uc2_network.get_node_by_hostname("database_server")
    db_service: DatabaseService = db_server.software_manager.software["DatabaseService"]

    # create a back up
    assert db_service.backup_database() is True

    db_service.db_file.corrupt()  # corrupt the db
    assert db_service.db_file.health_status == FileSystemItemHealthStatus.CORRUPT  # db file is actually corrupt
    assert db_service.db_file.visible_health_status == FileSystemItemHealthStatus.NONE  # not scanned yet

    db_service.db_file.scan()  # scan the db file

    # db file is corrupt since last scan
    assert db_service.db_file.visible_health_status == FileSystemItemHealthStatus.CORRUPT

    # back up should be restored
    assert db_service.restore_backup() is True

    assert db_service.db_file.health_status == FileSystemItemHealthStatus.GOOD  # db file is actually good
    # db file is corrupt since last scan
    assert db_service.db_file.visible_health_status == FileSystemItemHealthStatus.CORRUPT

    db_service.db_file.scan()  # scan the db file
    assert db_service.db_file.visible_health_status == FileSystemItemHealthStatus.GOOD  # now looks good


def test_restore_backup_after_deleting_file_without_updating_scan(uc2_network):
    """Same test as restore backup but the file is previously seen as corrupted."""
    db_server: Server = uc2_network.get_node_by_hostname("database_server")
    db_service: DatabaseService = db_server.software_manager.software["DatabaseService"]

    assert db_service.backup_database() is True

    db_service.db_file.corrupt()  # corrupt the db
    assert db_service.db_file.health_status == FileSystemItemHealthStatus.CORRUPT  # db file is actually corrupt
    assert db_service.db_file.visible_health_status == FileSystemItemHealthStatus.NONE  # not scanned yet

    db_service.db_file.scan()  # scan the db file

    # db file is corrupt since last scan
    assert db_service.db_file.visible_health_status == FileSystemItemHealthStatus.CORRUPT

    # delete database locally
    db_service.file_system.delete_file(folder_name="database", file_name="database.db")

    # db file is gone, reduced to atoms
    assert db_service.db_file is None

    # back up should be restored
    assert db_service.restore_backup() is True

    assert db_service.db_file.health_status == FileSystemItemHealthStatus.GOOD  # db file is actually good
    # db file is corrupt since last scan
    assert db_service.db_file.visible_health_status == FileSystemItemHealthStatus.CORRUPT

    db_service.db_file.scan()  # scan the db file
    assert db_service.db_file.visible_health_status == FileSystemItemHealthStatus.GOOD  # now looks good


def test_database_service_fix(uc2_network):
    """Test that the software fix applies to database service."""
    db_server: Server = uc2_network.get_node_by_hostname("database_server")
    db_service: DatabaseService = db_server.software_manager.software["DatabaseService"]

    assert db_service.backup_database() is True

    # delete database locally
    db_service.file_system.delete_file(folder_name="database", file_name="database.db")

    # db file is gone, reduced to atoms
    assert db_service.db_file is None

    db_service.fix()  # fix the database service

    assert db_service.health_state_actual == SoftwareHealthState.FIXING

    # apply timestep until the fix is applied
    for i in range(db_service.config.fixing_duration + 1):
        uc2_network.apply_timestep(i)

    assert db_service.db_file.health_status == FileSystemItemHealthStatus.GOOD
    assert db_service.health_state_actual == SoftwareHealthState.GOOD


def test_database_cannot_be_queried_while_fixing(uc2_network):
    """Tests that the database service cannot be queried if the service is being fixed."""
    db_server: Server = uc2_network.get_node_by_hostname("database_server")
    db_service: DatabaseService = db_server.software_manager.software["DatabaseService"]

    web_server: Server = uc2_network.get_node_by_hostname("web_server")
    db_client: DatabaseClient = web_server.software_manager.software["DatabaseClient"]

    db_connection: DatabaseClientConnection = db_client.get_new_connection()

    assert db_connection.query(sql="SELECT")

    assert db_service.backup_database() is True

    # delete database locally
    db_service.file_system.delete_file(folder_name="database", file_name="database.db")

    # db file is gone, reduced to atoms
    assert db_service.db_file is None

    db_service.fix()  # fix the database service
    assert db_service.health_state_actual == SoftwareHealthState.FIXING

    # fails to query because database is in FIXING state
    assert db_connection.query(sql="SELECT") is False

    # apply timestep until the fix is applied
    for i in range(db_service.config.fixing_duration + 1):
        uc2_network.apply_timestep(i)

    assert db_service.health_state_actual == SoftwareHealthState.GOOD

    assert db_service.db_file.health_status == FileSystemItemHealthStatus.GOOD

    assert db_connection.query(sql="SELECT")


def test_database_can_create_connection_while_fixing(uc2_network):
    """Tests that connections cannot be created while the database is being fixed."""
    db_server: Server = uc2_network.get_node_by_hostname("database_server")
    db_service: DatabaseService = db_server.software_manager.software["DatabaseService"]

    client_2: Server = uc2_network.get_node_by_hostname("client_2")
    db_client: DatabaseClient = client_2.software_manager.software["DatabaseClient"]

    db_connection: DatabaseClientConnection = db_client.get_new_connection()

    assert db_connection.query(sql="SELECT")

    assert db_service.backup_database() is True

    # delete database locally
    db_service.file_system.delete_file(folder_name="database", file_name="database.db")

    # db file is gone, reduced to atoms
    assert db_service.db_file is None

    db_service.fix()  # fix the database service
    assert db_service.health_state_actual == SoftwareHealthState.FIXING

    # fails to query because database is in FIXING state
    assert db_connection.query(sql="SELECT") is False

    # should be able to create a new connection
    new_db_connection: DatabaseClientConnection = db_client.get_new_connection()
    assert new_db_connection is not None
    assert new_db_connection.query(sql="SELECT") is False  # still should fail to query because FIXING

    # apply timestep until the fix is applied
    for i in range(db_service.config.fixing_duration + 1):
        uc2_network.apply_timestep(i)

    assert db_service.health_state_actual == SoftwareHealthState.GOOD
    assert db_service.db_file.health_status == FileSystemItemHealthStatus.GOOD

    assert db_connection.query(sql="SELECT")
    assert new_db_connection.query(sql="SELECT")


def test_database_client_cannot_query_offline_database_server(uc2_network):
    """Tests DB query across the network returns HTTP status 404 when db server is offline."""
    db_server: Server = uc2_network.get_node_by_hostname("database_server")
    db_service: DatabaseService = db_server.software_manager.software.get("DatabaseService")

    assert db_server.operating_state is NodeOperatingState.ON
    assert db_service.operating_state is ServiceOperatingState.RUNNING

    web_server: Server = uc2_network.get_node_by_hostname("web_server")
    db_client: DatabaseClient = web_server.software_manager.software.get("DatabaseClient")
    db_client.connect()
    assert len(db_client.client_connections)

    # Establish a new connection to the DatabaseService
    db_connection: DatabaseClientConnection = db_client.get_new_connection()

    assert db_connection.query("SELECT") is True
    assert db_connection.query("INSERT") is True
    db_server.power_off()

    for i in range(db_server.shut_down_duration + 1):
        uc2_network.apply_timestep(timestep=i)

    assert db_server.operating_state is NodeOperatingState.OFF
    assert db_service.operating_state is ServiceOperatingState.STOPPED

    assert db_connection.query("SELECT") is False
    assert db_connection.query("INSERT") is False


def test_database_client_uninstall_terminates_connections(peer_to_peer):
    node_a, node_b = peer_to_peer

    db_client: DatabaseClient = node_a.software_manager.software["DatabaseClient"]
    db_service: DatabaseService = node_b.software_manager.software["DatabaseService"]  # noqa

    db_connection: DatabaseClientConnection = db_client.get_new_connection()

    # Check that all connection counters are correct and that the client connection can query the database
    assert len(db_service.connections) == 1

    assert len(db_client.client_connections) == 1

    assert db_connection.is_active

    assert db_connection.query("SELECT")

    # Perform the DatabaseClient uninstall
    node_a.software_manager.uninstall("DatabaseClient")

    # Check that all connection counters are updated accordingly and client connection can no longer query the database
    assert len(db_service.connections) == 0

    assert len(db_client.client_connections) == 0

    assert not db_connection.query("SELECT")

    assert not db_connection.is_active


def test_database_service_can_terminate_connection(peer_to_peer):
    node_a, node_b = peer_to_peer

    db_client: DatabaseClient = node_a.software_manager.software["DatabaseClient"]
    db_service: DatabaseService = node_b.software_manager.software["DatabaseService"]  # noqa

    db_connection: DatabaseClientConnection = db_client.get_new_connection()

    # Check that all connection counters are correct and that the client connection can query the database
    assert len(db_service.connections) == 1

    assert len(db_client.client_connections) == 1

    assert db_connection.is_active

    assert db_connection.query("SELECT")

    # Perform the server-led connection termination
    connection_id = next(iter(db_service.connections.keys()))
    db_service.terminate_connection(connection_id)

    # Check that all connection counters are updated accordingly and client connection can no longer query the database
    assert len(db_service.connections) == 0

    assert len(db_client.client_connections) == 0

    assert not db_connection.query("SELECT")

    assert not db_connection.is_active


def test_client_connection_terminate_does_not_terminate_another_clients_connection():
    network = Network()

    db_server: Server = Server.from_config(config={"type":"server",
        "hostname":"db_client", "ip_address":"192.168.0.11", "subnet_mask":"255.255.255.0", "start_up_duration":0}
    )
    db_server.power_on()

    db_server.software_manager.install(DatabaseService)
    db_service: DatabaseService = db_server.software_manager.software["DatabaseService"]  # noqa
    db_service.start()

    client_a = Computer(
        hostname="client_a", ip_address="192.168.0.12", subnet_mask="255.255.255.0", start_up_duration=0
    )
    client_a.power_on()

    client_a.software_manager.install(DatabaseClient)
    client_a.software_manager.software["DatabaseClient"].configure(server_ip_address=IPv4Address("192.168.0.11"))
    client_a.software_manager.software["DatabaseClient"].run()

    client_b = Computer(
        hostname="client_b", ip_address="192.168.0.13", subnet_mask="255.255.255.0", start_up_duration=0
    )
    client_b.power_on()

    client_b.software_manager.install(DatabaseClient)
    client_b.software_manager.software["DatabaseClient"].configure(server_ip_address=IPv4Address("192.168.0.11"))
    client_b.software_manager.software["DatabaseClient"].run()

    switch = Switch(hostname="switch", start_up_duration=0, num_ports=3)
    switch.power_on()

    network.connect(endpoint_a=switch.network_interface[1], endpoint_b=db_server.network_interface[1])
    network.connect(endpoint_a=switch.network_interface[2], endpoint_b=client_a.network_interface[1])
    network.connect(endpoint_a=switch.network_interface[3], endpoint_b=client_b.network_interface[1])

    db_client_a: DatabaseClient = client_a.software_manager.software["DatabaseClient"]  # noqa
    db_connection_a = db_client_a.get_new_connection()

    assert db_connection_a.query("SELECT")
    assert len(db_service.connections) == 1

    db_client_b: DatabaseClient = client_b.software_manager.software["DatabaseClient"]  # noqa
    db_connection_b = db_client_b.get_new_connection()

    assert db_connection_b.query("SELECT")
    assert len(db_service.connections) == 2

    db_connection_a.disconnect()

    assert db_connection_b.query("SELECT")
    assert len(db_service.connections) == 1


def test_database_server_install_ftp_client():
    server: Server = Server.from_config(config={"type":"server", "hostname":"db_server", "ip_address":"192.168.1.2", "subnet_mask":"255.255.255.0", "start_up_duration":0})
    server.software_manager.install(DatabaseService)
    assert server.software_manager.software.get("FTPClient")
