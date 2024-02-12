from ipaddress import IPv4Address
from typing import Tuple
from uuid import uuid4

import pytest

from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.system.applications.application import ApplicationOperatingState
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.services.database.database_service import DatabaseService


@pytest.fixture(scope="function")
def database_client_on_computer() -> Tuple[DatabaseClient, Computer]:
    network = Network()

    db_server = Server(hostname="db_server", ip_address="192.168.0.1", subnet_mask="255.255.255.0", start_up_duration=0)
    db_server.power_on()
    db_server.software_manager.install(DatabaseService)
    db_server.software_manager.software["DatabaseService"].start()

    db_client = Computer(
        hostname="db_client", ip_address="192.168.0.2", subnet_mask="255.255.255.0", start_up_duration=0
    )
    db_client.power_on()
    db_client.software_manager.install(DatabaseClient)

    database_client: DatabaseClient = db_client.software_manager.software.get("DatabaseClient")
    database_client.configure(server_ip_address=IPv4Address("192.168.0.1"))
    database_client.run()

    network.connect(db_server.network_interface[1], db_client.network_interface[1])

    return database_client, db_client


def test_creation(database_client_on_computer):
    database_client, computer = database_client_on_computer
    database_client.describe_state()


def test_connect_when_client_is_closed(database_client_on_computer):
    """Database client should not connect when it is not running."""
    database_client, computer = database_client_on_computer

    database_client.close()
    assert database_client.operating_state is ApplicationOperatingState.CLOSED

    assert database_client.connect() is False


def test_connect_to_database_fails_on_reattempt(database_client_on_computer):
    """Database client should return False when the attempt to connect fails."""
    database_client, computer = database_client_on_computer

    database_client.connected = False
    assert database_client._connect(server_ip_address=IPv4Address("192.168.0.1"), is_reattempt=True) is False


def test_disconnect_when_client_is_closed(database_client_on_computer):
    """Database client disconnect should not do anything when it is not running."""
    database_client, computer = database_client_on_computer

    database_client.connect()
    assert database_client.server_ip_address is not None

    database_client.close()
    assert database_client.operating_state is ApplicationOperatingState.CLOSED

    database_client.disconnect()

    assert database_client.connected is True
    assert database_client.server_ip_address is not None


def test_disconnect(database_client_on_computer):
    """Database client should remove the connection."""
    database_client, computer = database_client_on_computer

    assert not database_client.connected

    database_client.connect()

    assert database_client.connected

    database_client.disconnect()

    assert not database_client.connected


def test_query_when_client_is_closed(database_client_on_computer):
    """Database client should return False when it is not running."""
    database_client, computer = database_client_on_computer

    database_client.close()
    assert database_client.operating_state is ApplicationOperatingState.CLOSED

    assert database_client.query(sql="test") is False


def test_query_fail_to_connect(database_client_on_computer):
    """Database client query should return False if the connect attempt fails."""
    database_client, computer = database_client_on_computer

    def return_false():
        return False

    database_client.connect = return_false
    database_client.connected = False

    assert database_client.query(sql="test") is False


def test_client_receives_response_when_closed(database_client_on_computer):
    """Database client receive should return False when it is closed."""
    database_client, computer = database_client_on_computer

    database_client.close()
    assert database_client.operating_state is ApplicationOperatingState.CLOSED

    database_client.receive(payload={}, session_id="")
