from ipaddress import IPv4Address
from typing import Tuple, Union

import pytest

from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.computer import Computer
from primaite.simulator.system.applications.application import ApplicationOperatingState
from primaite.simulator.system.applications.database_client import DatabaseClient


@pytest.fixture(scope="function")
def database_client_on_computer() -> Tuple[DatabaseClient, Computer]:
    computer = Computer(
        hostname="db_node", ip_address="192.168.0.1", subnet_mask="255.255.255.0", operating_state=NodeOperatingState.ON
    )
    computer.software_manager.install(DatabaseClient)

    database_client: DatabaseClient = computer.software_manager.software.get("DatabaseClient")
    database_client.configure(server_ip_address=IPv4Address("192.168.0.1"))
    database_client.run()
    return database_client, computer


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

    database_client.connected = True
    assert database_client.server_ip_address is not None

    database_client.close()
    assert database_client.operating_state is ApplicationOperatingState.CLOSED

    database_client.disconnect()

    assert database_client.connected is True
    assert database_client.server_ip_address is not None


def test_disconnect(database_client_on_computer):
    """Database client should set connected to False and remove the database server ip address."""
    database_client, computer = database_client_on_computer

    database_client.connected = True

    assert database_client.operating_state is ApplicationOperatingState.RUNNING
    assert database_client.server_ip_address is not None

    database_client.disconnect()

    assert database_client.connected is False
    assert database_client.server_ip_address is None


def test_query_when_client_is_closed(database_client_on_computer):
    """Database client should return False when it is not running."""
    database_client, computer = database_client_on_computer

    database_client.close()
    assert database_client.operating_state is ApplicationOperatingState.CLOSED

    assert database_client.query(sql="test") is False


def test_query_failed_reattempt(database_client_on_computer):
    """Database client query should return False if the reattempt fails."""
    database_client, computer = database_client_on_computer

    def return_false():
        return False

    database_client.connect = return_false

    database_client.connected = False
    assert database_client.query(sql="test", is_reattempt=True) is False


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
