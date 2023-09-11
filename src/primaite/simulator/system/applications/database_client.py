from ipaddress import IPv4Address
from typing import Any, Dict, Optional

from prettytable import PrettyTable

from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.application import Application
from primaite.simulator.system.core.software_manager import SoftwareManager


class DatabaseClient(Application):
    """
    A DatabaseClient application.

    Extends the Application class to provide functionality for connecting, querying, and disconnecting from a
    Database Service. It mainly operates over TCP protocol.

    :ivar server_ip_address: The IPv4 address of the Database Service server, defaults to None.
    """

    server_ip_address: Optional[IPv4Address] = None
    connected: bool = False

    def __init__(self, **kwargs):
        kwargs["name"] = "DatabaseClient"
        kwargs["port"] = Port.POSTGRES_SERVER
        kwargs["protocol"] = IPProtocol.TCP
        super().__init__(**kwargs)

    def describe_state(self) -> Dict:
        """
        Describes the current state of the ACLRule.

        :return: A dictionary representing the current state.
        """
        pass
        return super().describe_state()

    def connect(self, server_ip_address: IPv4Address, password: Optional[str] = None) -> bool:
        """
        Connect to a Database Service.

        :param server_ip_address: The IPv4 Address of the Node the Database Service is running on.
        :param password: The Database Service password. Is optional and has a default value of None.
        """
        if not self.connected and self.operating_state.RUNNING:
            return self._connect(server_ip_address, password)

    def _connect(
        self, server_ip_address: IPv4Address, password: Optional[str] = None, is_reattempt: bool = False
    ) -> bool:
        if is_reattempt:
            if self.connected:
                self.sys_log.info(f"DatabaseClient connected to {server_ip_address} authorised")
                self.server_ip_address = server_ip_address
                return self.connected
            else:
                self.sys_log.info(f"DatabaseClient connected to {server_ip_address} declined")
        payload = {"type": "connect_request", "password": password}
        software_manager: SoftwareManager = self.software_manager
        software_manager.send_payload_to_session_manager(
            payload=payload, dest_ip_address=server_ip_address, dest_port=self.port
        )
        return self._connect(server_ip_address, password, True)

    def disconnect(self):
        """Disconnect from the Database Service."""
        if self.connected and self.operating_state.RUNNING:
            software_manager: SoftwareManager = self.software_manager
            software_manager.send_payload_to_session_manager(
                payload={"type": "disconnect"}, dest_ip_address=self.server_ip_address, dest_port=self.port
            )

            self.sys_log.info(f"DatabaseClient disconnected from {self.server_ip_address}")
            self.server_ip_address = None

    def query(self, sql: str):
        """
        Send a query to the Database Service.

        :param sql: The SQL query.
        """
        if self.connected and self.operating_state.RUNNING:
            software_manager: SoftwareManager = self.software_manager
            software_manager.send_payload_to_session_manager(
                payload={"type": "sql", "sql": sql}, dest_ip_address=self.server_ip_address, dest_port=self.port
            )

    def _print_data(self, data: Dict):
        """
        Display the contents of the Folder in tabular format.

        :param markdown: Whether to display the table in Markdown format or not. Default is `False`.
        """
        table = PrettyTable(list(data.values())[0])

        table.align = "l"
        table.title = f"{self.sys_log.hostname} Database Client"
        for row in data.values():
            table.add_row(row.values())
        print(table)

    def receive(self, payload: Any, session_id: str, **kwargs) -> bool:
        """
        Receive a payload from the Software Manager.

        :param payload: A payload to receive.
        :param session_id: The session id the payload relates to.
        :return: True.
        """
        if isinstance(payload, dict) and payload.get("type"):
            if payload["type"] == "connect_response":
                self.connected = payload["response"] == True
            elif payload["type"] == "sql":
                self._print_data(payload["data"])
        return True
