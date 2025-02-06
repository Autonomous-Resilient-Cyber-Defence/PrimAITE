# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from typing import Any, Dict, List, Set

import yaml
from pydantic import Field

from primaite.game.game import PrimaiteGame
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.services.database.database_service import DatabaseService
from primaite.simulator.system.services.service import Service
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.port import PORT_LOOKUP
from tests import TEST_ASSETS_ROOT


class _DatabaseListener(Service, discriminator="database-listener"):
    class ConfigSchema(Service.ConfigSchema):
        """ConfigSchema for _DatabaseListener."""

        type: str = "database-listener"
        listen_on_ports: Set[int] = {PORT_LOOKUP["POSTGRES_SERVER"]}

    config: "_DatabaseListener.ConfigSchema" = Field(default_factory=lambda: _DatabaseListener.ConfigSchema())
    name: str = "database-listener"
    protocol: str = PROTOCOL_LOOKUP["TCP"]
    port: int = PORT_LOOKUP["NONE"]
    listen_on_ports: Set[int] = {PORT_LOOKUP["POSTGRES_SERVER"]}
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
    server_db = server.software_manager.software["database-service"]
    server_db.start()

    server.software_manager.install(_DatabaseListener)
    server_db_listener: _DatabaseListener = server.software_manager.software["database-listener"]
    server_db_listener.start()

    computer.software_manager.install(DatabaseClient)
    computer_db_client: DatabaseClient = computer.software_manager.software["database-client"]

    computer_db_client.run()
    computer_db_client.server_ip_address = server.network_interface[1].ip_address

    assert len(server_db_listener.payloads_received) == 0
    computer.session_manager.receive_payload_from_software_manager(
        payload="masquerade as Database traffic",
        dst_ip_address=server.network_interface[1].ip_address,
        dst_port=PORT_LOOKUP["POSTGRES_SERVER"],
        ip_protocol=PROTOCOL_LOOKUP["TCP"],
    )

    assert len(server_db_listener.payloads_received) == 1

    db_connection = computer_db_client.get_new_connection()

    assert db_connection

    assert len(server_db_listener.payloads_received) == 2

    assert db_connection.query("SELECT")

    assert len(server_db_listener.payloads_received) == 3


def test_set_listen_on_ports_from_config():
    config_path = TEST_ASSETS_ROOT / "configs" / "basic_node_with_software_listening_ports.yaml"

    with open(config_path, "r") as f:
        config_dict = yaml.safe_load(f)
    network = PrimaiteGame.from_config(cfg=config_dict).simulation.network

    client: Computer = network.get_node_by_hostname("client")
    assert PORT_LOOKUP["SMB"] in client.software_manager.get_open_ports()
    assert PORT_LOOKUP["IPP"] in client.software_manager.get_open_ports()

    web_browser = client.software_manager.software["web-browser"]

    assert not web_browser.listen_on_ports.difference({PORT_LOOKUP["SMB"], PORT_LOOKUP["IPP"]})
