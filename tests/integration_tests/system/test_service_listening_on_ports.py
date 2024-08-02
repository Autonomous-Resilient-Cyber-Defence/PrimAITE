# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from typing import Any, Dict, List, Set

from pydantic import Field

from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.services.database.database_service import DatabaseService
from primaite.simulator.system.services.service import Service


class _DatabaseListener(Service):
    name: str = "DatabaseListener"
    protocol: IPProtocol = IPProtocol.TCP
    port: Port = Port.NONE
    listen_on_ports: Set[Port] = {Port.POSTGRES_SERVER}
    payloads_received: List[Any] = Field(default_factory=list)

    def receive(self, payload: Any, session_id: str, **kwargs) -> bool:
        self.payloads_received.append(payload)
        self.sys_log.info(f"{self.name}: received payload {payload}")
        return True

    def describe_state(self) -> Dict:
        return super().describe_state()


def test_http_listener(client_server):
    computer, server = client_server

    server.software_manager.install(DatabaseService)
    server_db = server.software_manager.software["DatabaseService"]
    server_db.start()

    server.software_manager.install(_DatabaseListener)
    server_db_listener: _DatabaseListener = server.software_manager.software["DatabaseListener"]
    server_db_listener.start()

    computer.software_manager.install(DatabaseClient)
    computer_db_client: DatabaseClient = computer.software_manager.software["DatabaseClient"]

    computer_db_client.run()
    computer_db_client.server_ip_address = server.network_interface[1].ip_address

    assert len(server_db_listener.payloads_received) == 0
    computer.session_manager.receive_payload_from_software_manager(
        payload="masquerade as Database traffic",
        dst_ip_address=server.network_interface[1].ip_address,
        dst_port=Port.POSTGRES_SERVER,
        ip_protocol=IPProtocol.TCP,
    )

    assert len(server_db_listener.payloads_received) == 1

    db_connection = computer_db_client.get_new_connection()

    assert db_connection

    assert len(server_db_listener.payloads_received) == 2

    assert db_connection.query("SELECT")

    assert len(server_db_listener.payloads_received) == 3
