# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from __future__ import annotations

from ipaddress import IPv4Address
from typing import Any, Dict, Optional, Union
from uuid import uuid4

from prettytable import MARKDOWN, PrettyTable
from pydantic import BaseModel

from primaite.interface.request import RequestFormat, RequestResponse
from primaite.simulator.core import RequestManager, RequestType
from primaite.simulator.network.hardware.nodes.host.host_node import HostNode
from primaite.simulator.system.applications.application import Application
from primaite.simulator.system.core.software_manager import SoftwareManager
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.ipv4_address import IPV4Address
from primaite.utils.validation.port import PORT_LOOKUP


class DatabaseClientConnection(BaseModel):
    """
    DatabaseClientConnection Class.

    This class is used to record current DatabaseConnections within the DatabaseClient class.
    """

    connection_id: str
    """Connection UUID."""

    parent_node: HostNode
    """The parent Node that this connection was created on."""

    is_active: bool = True
    """Flag to state whether the connection is still active or not."""

    @property
    def client(self) -> Optional[DatabaseClient]:
        """The DatabaseClient that holds this connection."""
        return self.parent_node.software_manager.software.get("DatabaseClient")

    def query(self, sql: str) -> bool:
        """
        Query the databaseserver.

        :return: Boolean value
        """
        if self.is_active and self.client:
            return self.client._query(connection_id=self.connection_id, sql=sql)  # noqa
        return False

    def disconnect(self):
        """Disconnect the connection."""
        if self.client and self.is_active:
            self.client._disconnect(self.connection_id)  # noqa

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(connection_id='{self.connection_id}', is_active={self.is_active})"

    def __repr__(self) -> str:
        return str(self)


class DatabaseClient(Application, identifier="DatabaseClient"):
    """
    A DatabaseClient application.

    Extends the Application class to provide functionality for connecting, querying, and disconnecting from a
    Database Service. It mainly operates over TCP protocol.

    """

    config: "DatabaseClient.ConfigSchema" = None

    server_ip_address: Optional[IPv4Address] = None
    """The IPv4 address of the Database Service server, defaults to None."""
    server_password: Optional[str] = None
    _query_success_tracker: Dict[str, bool] = {}
    """Keep track of connections that were established or verified during this step. Used for rewards."""
    last_query_response: Optional[Dict] = None
    """Keep track of the latest query response. Used to determine rewards."""
    _server_connection_id: Optional[str] = None
    """Connection ID to the Database Server."""
    client_connections: Dict[str, DatabaseClientConnection] = {}
    """Keep track of active connections to Database Server."""
    _client_connection_requests: Dict[str, Optional[Union[str, DatabaseClientConnection]]] = {}
    """Dictionary of connection requests to Database Server."""
    connected: bool = False
    """Boolean Value for whether connected to DB Server."""
    native_connection: Optional[DatabaseClientConnection] = None
    """Native Client Connection for using the client directly (similar to psql in a terminal)."""

    class ConfigSchema(Application.ConfigSchema):
        """ConfigSchema for DatabaseClient."""

        type: str = "DATABASE_CLIENT"

    def __init__(self, **kwargs):
        kwargs["name"] = "DatabaseClient"
        kwargs["port"] = PORT_LOOKUP["POSTGRES_SERVER"]
        kwargs["protocol"] = PROTOCOL_LOOKUP["TCP"]
        super().__init__(**kwargs)

    def _init_request_manager(self) -> RequestManager:
        """
        Initialise the request manager.

        More information in user guide and docstring for SimComponent._init_request_manager.
        """
        rm = super()._init_request_manager()
        rm.add_request("execute", RequestType(func=lambda request, context: RequestResponse.from_bool(self.execute())))

        def _configure(request: RequestFormat, context: Dict) -> RequestResponse:
            ip, pw = request[-1].get("server_ip_address"), request[-1].get("server_password")
            ip = None if ip is None else IPV4Address(ip)
            success = self.configure(server_ip_address=ip, server_password=pw)
            return RequestResponse.from_bool(success)

        rm.add_request("configure", RequestType(func=_configure))
        return rm

    def execute(self) -> bool:
        """Execution definition for db client: perform a select query."""
        if not self._can_perform_action():
            return False

        self.num_executions += 1  # trying to connect counts as an execution

        if not self.native_connection:
            self.connect()

        if self.native_connection:
            return self.check_connection(connection_id=self.native_connection.connection_id)

        return False

    def describe_state(self) -> Dict:
        """
        Describes the current state of the ACLRule.

        :return: A dictionary representing the current state.
        """
        state = super().describe_state()
        return state

    def show(self, markdown: bool = False):
        """
        Display the client connections in tabular format.

        :param markdown: Whether to display the table in Markdown format or not. Default is `False`.
        """
        table = PrettyTable(["Connection ID", "Active"])
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.sys_log.hostname} {self.name} Client Connections"
        if self.native_connection:
            table.add_row([self.native_connection.connection_id, self.native_connection.is_active])
        for connection_id, connection in self.client_connections.items():
            table.add_row([connection_id, connection.is_active])
        print(table.get_string(sortby="Connection ID"))

    def configure(self, server_ip_address: Optional[IPv4Address] = None, server_password: Optional[str] = None) -> bool:
        """
        Configure the DatabaseClient to communicate with a DatabaseService.

        :param server_ip_address: The IP address of the Node the DatabaseService is on.
        :param server_password: The password on the DatabaseService.
        """
        self.server_ip_address = server_ip_address or self.server_ip_address
        self.server_password = server_password or self.server_password
        self.sys_log.info(f"{self.name}: Configured the {self.name} with {server_ip_address=}, {server_password=}.")
        return True

    def connect(self) -> bool:
        """Connect the native client connection."""
        if self.native_connection:
            return True
        self.native_connection = self.get_new_connection()
        return self.native_connection is not None

    def disconnect(self):
        """Disconnect the native client connection."""
        if self.native_connection:
            self._disconnect(self.native_connection.connection_id)
            self.native_connection = None

    def check_connection(self, connection_id: str) -> bool:
        """Check whether the connection can be successfully re-established.

        :param connection_id: connection ID to check
        :type connection_id: str
        :return: Whether the connection was successfully re-established.
        :rtype: bool
        """
        if not self._can_perform_action():
            return False
        return self._query("SELECT * FROM pg_stat_activity", connection_id=connection_id)

    def _validate_client_connection_request(self, connection_id: str) -> bool:
        """Check that client_connection_id is valid."""
        return True if connection_id in self._client_connection_requests else False

    def _connect(
        self,
        server_ip_address: IPv4Address,
        connection_request_id: str,
        password: Optional[str] = None,
        is_reattempt: bool = False,
    ) -> Optional[DatabaseClientConnection]:
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
            valid_connection_request = self._validate_client_connection_request(connection_id=connection_request_id)
            if valid_connection_request:
                database_client_connection = self._client_connection_requests.pop(connection_request_id)
                if isinstance(database_client_connection, DatabaseClientConnection):
                    self.sys_log.info(
                        f"{self.name}: Connection request ({connection_request_id}) to {server_ip_address} authorised. "
                        f"Using connection id {database_client_connection}"
                    )
                    self.connected = True
                    return database_client_connection
                else:
                    self.sys_log.info(
                        f"{self.name}: Connection request ({connection_request_id}) to {server_ip_address} declined"
                    )
                    return None
            else:
                self.sys_log.info(
                    f"{self.name}: Connection request ({connection_request_id}) to {server_ip_address} declined "
                    f"due to unknown client-side connection request id"
                )
                return None

        payload = {"type": "connect_request", "password": password, "connection_request_id": connection_request_id}
        software_manager: SoftwareManager = self.software_manager
        software_manager.send_payload_to_session_manager(
            payload=payload, dest_ip_address=server_ip_address, dest_port=self.port
        )
        return self._connect(
            server_ip_address=server_ip_address,
            password=password,
            is_reattempt=True,
            connection_request_id=connection_request_id,
        )

    def _disconnect(self, connection_id: str) -> bool:
        """Disconnect from the Database Service.

        If no connection_id is provided, connect from first ID in
        self.client_connections.

        :param: connection_id: connection ID to disconnect.
        :type: connection_id: str

        :return: bool
        """
        if not self._can_perform_action():
            return False

        # if there are no connections - nothing to disconnect
        if len(self.client_connections) == 0:
            self.sys_log.warning(f"{self.name}: Unable to disconnect, no active connections.")
            return False
        if not self.client_connections.get(connection_id):
            return False
        software_manager: SoftwareManager = self.software_manager
        software_manager.send_payload_to_session_manager(
            payload={"type": "disconnect", "connection_id": connection_id},
            dest_ip_address=self.server_ip_address,
            dest_port=self.port,
        )
        connection = self.client_connections.pop(connection_id)
        self.terminate_connection(connection_id=connection_id)

        connection.is_active = False

        self.sys_log.info(f"{self.name}: DatabaseClient disconnected {connection_id} from {self.server_ip_address}")
        self.connected = False
        return True

    def uninstall(self) -> None:
        """
        Uninstall the DatabaseClient.

        Calls disconnect on all client connections to ensure that both client and server connections are killed.
        """
        while self.client_connections:
            conn_key = next(iter(self.client_connections.keys()))
            conn_obj: DatabaseClientConnection = self.client_connections[conn_key]
            conn_obj.disconnect()
            if conn_obj.is_active or conn_key in self.client_connections:
                self.sys_log.error(
                    "Attempted to uninstall database client but could not drop active connections. "
                    "Forcing uninstall anyway."
                )
                self.client_connections.pop(conn_key, None)
        super().uninstall()

    def get_new_connection(self) -> Optional[DatabaseClientConnection]:
        """Get a new connection to the DatabaseServer.

        :return: DatabaseClientConnection object
        """
        if not self._can_perform_action():
            return None

        connection_request_id = str(uuid4())
        self._client_connection_requests[connection_request_id] = None

        self.sys_log.info(
            f"{self.name}: Sending new connection request ({connection_request_id}) to {self.server_ip_address}"
        )

        return self._connect(
            server_ip_address=self.server_ip_address,
            password=self.server_password,
            connection_request_id=connection_request_id,
        )

    def _create_client_connection(self, connection_id: str, connection_request_id: str) -> None:
        """Create a new DatabaseClientConnection Object."""
        client_connection = DatabaseClientConnection(
            connection_id=connection_id, client=self, parent_node=self.software_manager.node
        )
        self.client_connections[connection_id] = client_connection
        self._client_connection_requests[connection_request_id] = client_connection

    def _query(self, sql: str, connection_id: str, query_id: Optional[str] = False, is_reattempt: bool = False) -> bool:
        """
        Send a query to the connected database server.

        :param: sql: SQL query to send to the database server.
        :type: sql: str

        :param: query_id: ID of the query, used as reference
        :type: query_id: str

        :param: connection_id: ID of the connection to the database server.
        :type: connection_id: str

        :param: is_reattempt: True if the query request has been reattempted. Default False
        :type: is_reattempt: Optional[bool]
        """
        if not query_id:
            query_id = str(uuid4())
        if is_reattempt:
            success = self._query_success_tracker.get(query_id)
            if success:
                self.sys_log.info(f"{self.name}: Query successful {sql}")
                return True
            self.sys_log.error(f"{self.name}: Unable to run query {sql}")
            return False
        else:
            software_manager: SoftwareManager = self.software_manager
            software_manager.send_payload_to_session_manager(
                payload={"type": "sql", "sql": sql, "uuid": query_id, "connection_id": connection_id},
                dest_ip_address=self.server_ip_address,
                dest_port=self.port,
            )
            return self._query(sql=sql, query_id=query_id, connection_id=connection_id, is_reattempt=True)

    def run(self) -> None:
        """Run the DatabaseClient."""
        super().run()

    def query(self, sql: str) -> bool:
        """
        Send a query to the Database Service.

        :param: sql: The SQL query.
        :type: sql: str

        :return: True if the query was successful, otherwise False.
        """
        if not self._can_perform_action():
            return False

        if not self.native_connection:
            return False

        # reset last query response
        self.last_query_response = None

        uuid = str(uuid4())
        self._query_success_tracker[uuid] = False
        return self.native_connection.query(sql)

    def receive(self, session_id: str, payload: Any, **kwargs) -> bool:
        """
        Receive a payload from the Software Manager.

        :param payload: A payload to receive.
        :param session_id: The session id the payload relates to.
        :return: True.
        """
        if not self._can_perform_action():
            return False
        if isinstance(payload, dict) and payload.get("type"):
            if payload["type"] == "connect_response":
                if payload["response"] is True:
                    # add connection
                    connection_id = payload["connection_id"]
                    self._create_client_connection(
                        connection_id=connection_id, connection_request_id=payload["connection_request_id"]
                    )
            elif payload["type"] == "sql":
                self.last_query_response = payload
                query_id = payload.get("uuid")
                status_code = payload.get("status_code")
                self._query_success_tracker[query_id] = status_code == 200
                if self._query_success_tracker[query_id]:
                    self.sys_log.debug(f"Received {payload=}")
            elif payload["type"] == "disconnect":
                connection_id = payload["connection_id"]
                self.sys_log.info(f"{self.name}: Received disconnect command for {connection_id=} from the server")
                self._disconnect(payload["connection_id"])
        return True
