from ipaddress import IPv4Address

from primaite.simulator.network.hardware.nodes.server import Server
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.services.database import DatabaseService


def test_database_client_server_connection(uc2_network):
    web_server: Server = uc2_network.get_node_by_hostname("web_server")
    db_client: DatabaseClient = web_server.software_manager.software["DatabaseClient"]

    db_server: Server = uc2_network.get_node_by_hostname("database_server")
    db_service: DatabaseService = db_server.software_manager.software["DatabaseService"]

    assert len(db_service.connections) == 0

    assert db_client.connect(server_ip_address=IPv4Address("192.168.1.14"))
    assert len(db_service.connections) == 1

    db_client.disconnect()
    assert len(db_service.connections) == 0


def test_database_client_query(uc2_network):
    """Tests DB query across the network returns HTTP status 200 and date."""
    web_server: Server = uc2_network.get_node_by_hostname("web_server")
    db_client: DatabaseClient = web_server.software_manager.software["DatabaseClient"]

    db_client.connect(server_ip_address=IPv4Address("192.168.1.14"))

    db_client.query("SELECT * FROM user;")

    web_server_nic = web_server.ethernet_port[1]

    web_server_last_payload = web_server_nic.pcap.read()[-1]["payload"]

    assert web_server_last_payload["status_code"] == 200
    assert web_server_last_payload["data"]
