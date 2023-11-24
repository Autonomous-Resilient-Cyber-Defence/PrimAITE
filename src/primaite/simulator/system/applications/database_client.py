from ipaddress import IPv4Address
from typing import Any, Dict, Optional
from uuid import uuid4

from prettytable import PrettyTable

from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.application import Application, ApplicationOperatingState
from primaite.simulator.system.core.software_manager import SoftwareManager


class DatabaseClient(Application):
    """
    A DatabaseClient application.

    Extends the Application class to provide functionality for connecting, querying, and disconnecting from a
    Database Service. It mainly operates over TCP protocol.

    :ivar server_ip_address: The IPv4 address of the Database Service server, defaults to None.
    """

    server_ip_address: Optional[IPv4Address] = None
    server_password: Optional[str] = None
    connected: bool = False
    _query_success_tracker: Dict[str, bool] = {}

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

    def configure(self, server_ip_address: IPv4Address, server_password: Optional[str] = None):
        """
        Configure the DatabaseClient to communicate with a DatabaseService.

        :param server_ip_address: The IP address of the Node the DatabaseService is on.
        :param server_password: The password on the DatabaseService.
        """
        self.server_ip_address = server_ip_address
        self.server_password = server_password
        self.sys_log.info(f"{self.name}: Configured the {self.name} with {server_ip_address=}, {server_password=}.")

    def connect(self) -> bool:
        """Connect to a Database Service."""
        if not self.connected and self.operating_state.RUNNING:
            return self._connect(self.server_ip_address, self.server_password)
        return False

    def _connect(
        self, server_ip_address: IPv4Address, password: Optional[str] = None, is_reattempt: bool = False
    ) -> bool:
        """
        Connects the DatabaseClient to the DatabaseServer.

        :param: server_ip_address: IP address of the database server
        :type: server_ip_address: IPv4Address

        :param: password: Password used to connect to the database server. Optional.
        :type: password: Optional[str]

        :param: is_reattempt: True if the connect request has been reattempted. Default False
        :type: is_reattempt: Optional[bool]
        """
        if is_reattempt:
            if self.connected:
                self.sys_log.info(f"{self.name}: DatabaseClient connected to {server_ip_address} authorised")
                self.server_ip_address = server_ip_address
                return self.connected
            else:
                self.sys_log.info(f"{self.name}: DatabaseClient connected to {server_ip_address} declined")
                return False
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

            self.sys_log.info(f"{self.name}: DatabaseClient disconnected from {self.server_ip_address}")
            self.server_ip_address = None
            self.connected = False

    def _query(self, sql: str, query_id: str, is_reattempt: bool = False) -> bool:
        """
        Send a query to the connected database server.

        :param: sql: SQL query to send to the database server.
        :type: sql: str

        :param: query_id: ID of the query, used as reference
        :type: query_id: str

        :param: is_reattempt: True if the query request has been reattempted. Default False
        :type: is_reattempt: Optional[bool]
        """
        if is_reattempt:
            success = self._query_success_tracker.get(query_id)
            if success:
                self.sys_log.info(f"{self.name}: Query successful {sql}")
                return True
            self.sys_log.info(f"{self.name}: Unable to run query {sql}")
            return False
        else:
            software_manager: SoftwareManager = self.software_manager
            software_manager.send_payload_to_session_manager(
                payload={"type": "sql", "sql": sql, "uuid": query_id},
                dest_ip_address=self.server_ip_address,
                dest_port=self.port,
            )
            return self._query(sql=sql, query_id=query_id, is_reattempt=True)

    def execute(self) -> None:
        """Run the DatabaseClient."""
        # super().execute()
        if self.operating_state == ApplicationOperatingState.RUNNING:
            self.connect()

    def query(self, sql: str) -> bool:
        """
        Send a query to the Database Service.

        :param sql: The SQL query.
        :return: True if the query was successful, otherwise False.
        """
        if self.connected and self.operating_state == ApplicationOperatingState.RUNNING:
            query_id = str(uuid4())

            # Initialise the tracker of this ID to False
            self._query_success_tracker[query_id] = False
            return self._query(sql=sql, query_id=query_id)

    def _print_data(self, data: Dict):
        """
        Display the contents of the Folder in tabular format.

        :param markdown: Whether to display the table in Markdown format or not. Default is `False`.
        """
        if data:
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
                query_id = payload.get("uuid")
                status_code = payload.get("status_code")
                self._query_success_tracker[query_id] = status_code == 200
                if self._query_success_tracker[query_id]:
                    self._print_data(payload["data"])
        return True
