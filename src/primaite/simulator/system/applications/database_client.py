from ipaddress import IPv4Address
from typing import Any, Dict, Optional
from uuid import uuid4

from primaite import getLogger
from primaite.interface.request import RequestResponse
from primaite.simulator.core import RequestManager, RequestType
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.application import Application
from primaite.simulator.system.core.software_manager import SoftwareManager

_LOGGER = getLogger(__name__)


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
    _last_connection_successful: Optional[bool] = None
    """Keep track of connections that were established or verified during this step. Used for rewards."""
    last_query_response: Optional[Dict] = None
    """Keep track of the latest query response. Used to determine rewards."""
    _server_connection_id: Optional[str] = None

    def __init__(self, **kwargs):
        kwargs["name"] = "DatabaseClient"
        kwargs["port"] = Port.POSTGRES_SERVER
        kwargs["protocol"] = IPProtocol.TCP
        super().__init__(**kwargs)

    def _init_request_manager(self) -> RequestManager:
        """
        Initialise the request manager.

        More information in user guide and docstring for SimComponent._init_request_manager.
        """
        rm = super()._init_request_manager()
        rm.add_request("execute", RequestType(func=lambda request, context: RequestResponse.from_bool(self.execute())))
        return rm

    def execute(self) -> bool:
        """Execution definition for db client: perform a select query."""
        self.num_executions += 1  # trying to connect counts as an execution
        if not self._server_connection_id:
            self.connect()
        can_connect = self.check_connection(connection_id=self._server_connection_id)
        self._last_connection_successful = can_connect
        return can_connect

    def describe_state(self) -> Dict:
        """
        Describes the current state of the ACLRule.

        :return: A dictionary representing the current state.
        """
        state = super().describe_state()
        # list of connections that were established or verified during this step.
        state["last_connection_successful"] = self._last_connection_successful
        return state

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
        if not self._can_perform_action():
            return False

        if not self._server_connection_id:
            self._server_connection_id = str(uuid4())

        self.connected = self._connect(
            server_ip_address=self.server_ip_address,
            password=self.server_password,
            connection_id=self._server_connection_id,
        )
        if not self.connected:
            self._server_connection_id = None
        return self.connected

    def check_connection(self, connection_id: str) -> bool:
        """Check whether the connection can be successfully re-established.

        :param connection_id: connection ID to check
        :type connection_id: str
        :return: Whether the connection was successfully re-established.
        :rtype: bool
        """
        if not self._can_perform_action():
            return False
        return self.query("SELECT * FROM pg_stat_activity", connection_id=connection_id)

    def _connect(
        self,
        server_ip_address: IPv4Address,
        connection_id: Optional[str] = None,
        password: Optional[str] = None,
        is_reattempt: bool = False,
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
            if self._server_connection_id:
                self.sys_log.info(
                    f"{self.name} {connection_id=}: DatabaseClient connection to {server_ip_address} authorised"
                )
                self.server_ip_address = server_ip_address
                return True
            else:
                self.sys_log.info(
                    f"{self.name} {connection_id=}: DatabaseClient connection to {server_ip_address} declined"
                )
                return False
        payload = {
            "type": "connect_request",
            "password": password,
            "connection_id": connection_id,
        }
        software_manager: SoftwareManager = self.software_manager
        software_manager.send_payload_to_session_manager(
            payload=payload, dest_ip_address=server_ip_address, dest_port=self.port
        )
        return self._connect(
            server_ip_address=server_ip_address, password=password, connection_id=connection_id, is_reattempt=True
        )

    def disconnect(self) -> bool:
        """Disconnect from the Database Service."""
        if not self._can_perform_action():
            self.sys_log.error(f"Unable to disconnect - {self.name} is {self.operating_state.name}")
            return False

        # if there are no connections - nothing to disconnect
        if not self._server_connection_id:
            self.sys_log.error(f"Unable to disconnect - {self.name} has no active connections.")
            return False

        # if no connection provided, disconnect the first connection
        software_manager: SoftwareManager = self.software_manager
        software_manager.send_payload_to_session_manager(
            payload={"type": "disconnect", "connection_id": self._server_connection_id},
            dest_ip_address=self.server_ip_address,
            dest_port=self.port,
        )
        self.remove_connection(connection_id=self._server_connection_id)

        self.sys_log.info(
            f"{self.name}: DatabaseClient disconnected {self._server_connection_id} from {self.server_ip_address}"
        )
        self.connected = False

    def _query(self, sql: str, query_id: str, connection_id: str, is_reattempt: bool = False) -> bool:
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
                payload={"type": "sql", "sql": sql, "uuid": query_id, "connection_id": connection_id},
                dest_ip_address=self.server_ip_address,
                dest_port=self.port,
            )
            return self._query(sql=sql, query_id=query_id, connection_id=connection_id, is_reattempt=True)

    def run(self) -> None:
        """Run the DatabaseClient."""
        super().run()

    def query(self, sql: str, connection_id: Optional[str] = None) -> bool:
        """
        Send a query to the Database Service.

        :param: sql: The SQL query.
        :param: is_reattempt: If true, the action has been reattempted.
        :return: True if the query was successful, otherwise False.
        """
        if not self._can_perform_action():
            return False

        # reset last query response
        self.last_query_response = None

        connection_id: str

        if not connection_id:
            connection_id = self._server_connection_id

        if not connection_id:
            self.connect()
            connection_id = self._server_connection_id

        if not connection_id:
            msg = "Cannot run sql query, could not establish connection with the server."
            self.parent.sys_log(msg)
            return False

        uuid = str(uuid4())
        self._query_success_tracker[uuid] = False
        return self._query(sql=sql, query_id=uuid, connection_id=connection_id)

    def receive(self, payload: Any, session_id: str, **kwargs) -> bool:
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
                    self.add_connection(connection_id=payload.get("connection_id"), session_id=session_id)
            elif payload["type"] == "sql":
                self.last_query_response = payload
                query_id = payload.get("uuid")
                status_code = payload.get("status_code")
                self._query_success_tracker[query_id] = status_code == 200
                if self._query_success_tracker[query_id]:
                    _LOGGER.debug(f"Received payload {payload}")
        return True
