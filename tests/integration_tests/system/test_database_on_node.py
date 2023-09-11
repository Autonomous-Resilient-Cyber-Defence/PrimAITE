from ipaddress import IPv4Address

from primaite.simulator.network.hardware.nodes.server import Server
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.services.database_service import DatabaseService


def test_database_client_server_connection(uc2_network):
    web_server: Server = uc2_network.get_node_by_hostname("web_server")
    db_client: DatabaseClient = web_server.software_manager.software["DatabaseClient"]

    db_server: Server = uc2_network.get_node_by_hostname("database_server")
    db_service: DatabaseService = db_server.software_manager.software["DatabaseService"]

    assert len(db_service.connections) == 1

    db_client.disconnect()
    assert len(db_service.connections) == 0


def test_database_client_server_correct_password(uc2_network):
    web_server: Server = uc2_network.get_node_by_hostname("web_server")
    db_client: DatabaseClient = web_server.software_manager.software["DatabaseClient"]

    db_server: Server = uc2_network.get_node_by_hostname("database_server")
    db_service: DatabaseService = db_server.software_manager.software["DatabaseService"]

    db_client.disconnect()

    db_client.configure(server_ip_address=IPv4Address("192.168.1.14"), server_password="12345")
    db_service.password = "12345"

    assert db_client.connect()

    assert len(db_service.connections) == 1


def test_database_client_server_incorrect_password(uc2_network):
    web_server: Server = uc2_network.get_node_by_hostname("web_server")
    db_client: DatabaseClient = web_server.software_manager.software["DatabaseClient"]

    db_server: Server = uc2_network.get_node_by_hostname("database_server")
    db_service: DatabaseService = db_server.software_manager.software["DatabaseService"]

    db_client.disconnect()
    db_client.configure(server_ip_address=IPv4Address("192.168.1.14"), server_password="54321")
    db_service.password = "12345"

    assert not db_client.connect()
    assert len(db_service.connections) == 0


def test_database_client_query(uc2_network):
    """Tests DB query across the network returns HTTP status 200 and date."""
    web_server: Server = uc2_network.get_node_by_hostname("web_server")
    db_client: DatabaseClient = web_server.software_manager.software["DatabaseClient"]
    db_client.connect()

    assert db_client.query("SELECT * FROM user;")
