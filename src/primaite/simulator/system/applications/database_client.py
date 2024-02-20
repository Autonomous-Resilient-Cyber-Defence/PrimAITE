from ipaddress import IPv4Address
from typing import Any, Dict, Optional
from uuid import uuid4

from primaite import getLogger
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
    _query_success_tracker: Dict[str, bool] = {}

    def __init__(self, **kwargs):
        kwargs["name"] = "DatabaseClient"
        kwargs["port"] = Port.POSTGRES_SERVER
        kwargs["protocol"] = IPProtocol.TCP
        super().__init__(**kwargs)
        self.set_original_state()

    def set_original_state(self):
        """Sets the original state."""
        _LOGGER.debug(f"Setting DatabaseClient WebServer original state on node {self.software_manager.node.hostname}")
        super().set_original_state()
        vals_to_include = {"server_ip_address", "server_password", "connected", "_query_success_tracker"}
        self._original_state.update(self.model_dump(include=vals_to_include))

    def reset_component_for_episode(self, episode: int):
        """Reset the original state of the SimComponent."""
        _LOGGER.debug(f"Resetting DataBaseClient state on node {self.software_manager.node.hostname}")
        super().reset_component_for_episode(episode)
        self._query_success_tracker.clear()

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

    def connect(self, connection_id: Optional[str] = None) -> bool:
        """Connect to a Database Service."""
        if not self._can_perform_action():
            return False

        if not connection_id:
            connection_id = str(uuid4())

        return self._connect(
            server_ip_address=self.server_ip_address, password=self.server_password, connection_id=connection_id
        )

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
            if self.connections.get(connection_id):
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

    def disconnect(self, connection_id: Optional[str] = None) -> bool:
        """Disconnect from the Database Service."""
        if not self._can_perform_action():
            self.sys_log.error(f"Unable to disconnect - {self.name} is {self.operating_state.name}")
            return False

        # if there are no connections - nothing to disconnect
        if not len(self.connections):
            self.sys_log.error(f"Unable to disconnect - {self.name} has no active connections.")
            return False

        # if no connection provided, disconnect the first connection
        if not connection_id:
            connection_id = list(self.connections.keys())[0]

        software_manager: SoftwareManager = self.software_manager
        software_manager.send_payload_to_session_manager(
            payload={"type": "disconnect", "connection_id": connection_id},
            dest_ip_address=self.server_ip_address,
            dest_port=self.port,
        )
        self.remove_connection(connection_id=connection_id)

        self.sys_log.info(
            f"{self.name}: DatabaseClient disconnected connection {connection_id} from {self.server_ip_address}"
        )

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

        if connection_id is None:
            if self.connections:
                connection_id = list(self.connections.keys())[-1]
                # TODO: if the most recent connection dies, it should be automatically cleared.
            else:
                connection_id = str(uuid4())

        if not self.connections.get(connection_id):
            if not self.connect(connection_id=connection_id):
                return False

            # Initialise the tracker of this ID to False
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
                query_id = payload.get("uuid")
                status_code = payload.get("status_code")
                self._query_success_tracker[query_id] = status_code == 200
                if self._query_success_tracker[query_id]:
                    _LOGGER.debug(f"Received payload {payload}")
        return True
