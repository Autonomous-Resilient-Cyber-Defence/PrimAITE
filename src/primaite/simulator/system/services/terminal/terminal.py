# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from __future__ import annotations

from ipaddress import IPv4Address
from typing import Any, Dict, List, Optional
from uuid import uuid4

from prettytable import MARKDOWN, PrettyTable
from pydantic import BaseModel

from primaite.interface.request import RequestResponse
from primaite.simulator.core import RequestManager, RequestType
from primaite.simulator.network.hardware.base import Node
from primaite.simulator.network.protocols.ssh import (
    SSHConnectionMessage,
    SSHPacket,
    SSHTransportMessage,
    SSHUserCredentials,
)
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.core.software_manager import SoftwareManager
from primaite.simulator.system.services.service import Service, ServiceOperatingState
from primaite.simulator.system.software import SoftwareHealthState


class TerminalClientConnection(BaseModel):
    """
    TerminalClientConnection Class.

    This class is used to record current User Connections to the Terminal class.
    """

    parent_node: Node  # Technically should be HostNode but this causes circular import error.
    """The parent Node that this connection was created on."""

    dest_ip_address: IPv4Address = None
    """Destination IP address of connection"""

    session_id: str = None
    """Session ID that connection is linked to"""

    _connection_uuid: str = None
    """Connection UUID"""

    @property
    def client(self) -> Optional[Terminal]:
        """The Terminal that holds this connection."""
        return self.parent_node.software_manager.software.get("Terminal")

    def disconnect(self):
        """Disconnect the connection."""
        if self.client:
            self.client._disconnect(self._connection_uuid)  # noqa


class Terminal(Service):
    """Class used to simulate a generic terminal service. Can be interacted with by other terminals via SSH."""

    operating_state: ServiceOperatingState = ServiceOperatingState.RUNNING
    "Initial Operating State"

    health_state_actual: SoftwareHealthState = SoftwareHealthState.GOOD
    "Service Health State"

    _connections: Dict[str, TerminalClientConnection] = {}
    "List of active connections held on this terminal."

    def __init__(self, **kwargs):
        kwargs["name"] = "Terminal"
        kwargs["port"] = Port.SSH
        kwargs["protocol"] = IPProtocol.TCP
        super().__init__(**kwargs)

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        Please see :py:meth:`primaite.simulator.core.SimComponent.describe_state` for a more detailed explanation.

        :return: Current state of this object and child objects.
        :rtype: Dict
        """
        state = super().describe_state()
        return state

    def show(self, markdown: bool = False):
        """
        Display the remote connections to this terminal instance in tabular format.

        :param markdown: Whether to display the table in Markdown format or not. Default is `False`.
        """
        table = PrettyTable(["Connection ID", "Session_ID"])
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.sys_log.hostname} {self.name} Connections"
        for connection_id, connection in self._connections.items():
            table.add_row([connection_id, connection.session_id])
        print(table.get_string(sortby="Connection ID"))

    def _init_request_manager(self) -> RequestManager:
        """Initialise Request manager."""
        rm = super()._init_request_manager()
        rm.add_request(
            "send",
            request_type=RequestType(func=lambda request, context: RequestResponse.from_bool(self.send())),
        )

        def _login(request: List[Any], context: Any) -> RequestResponse:
            login = self._process_local_login(username=request[0], password=request[1])
            if login:
                return RequestResponse(status="success", data={})
            else:
                return RequestResponse(status="failure", data={})

        def _remote_login(request: List[Any], context: Any) -> RequestResponse:
            login = self._send_remote_login(username=request[0], password=request[1], ip_address=request[2])
            if login:
                return RequestResponse(status="success", data={})
            else:
                return RequestResponse(status="failure", data={})

        def _execute_request(request: List[Any], context: Any) -> RequestResponse:
            """Execute an instruction."""
            command: str = request[0]
            self.execute(command)
            return RequestResponse(status="success", data={})

        def _logoff(request: List[Any]) -> RequestResponse:
            """Logoff from connection."""
            connection_uuid = request[0]
            # TODO: Uncomment this when UserSessionManager merged.
            # self.parent.UserSessionManager.logoff(connection_uuid)
            self.disconnect(connection_uuid)

            return RequestResponse(status="success", data={})

        rm.add_request(
            "Login",
            request_type=RequestType(func=_login),
        )

        rm.add_request(
            "Remote Login",
            request_type=RequestType(func=_remote_login),
        )

        rm.add_request(
            "Execute",
            request_type=RequestType(func=_execute_request),
        )

        rm.add_request("Logoff", request_type=RequestType(func=_logoff))

        return rm

    def _add_new_connection(self, connection_uuid: str, session_id: str):
        """Create a new connection object and amend to list of active connections."""
        self._connections[connection_uuid] = TerminalClientConnection(
            parent_node=self.software_manager.node,
            connection_uuid=connection_uuid,
            session_id=session_id,
        )

    def login(self, username: str, password: str, ip_address: Optional[IPv4Address] = None) -> bool:
        """Process User request to login to Terminal.

        If ip_address is passed, login will attempt a remote login to the node at that address.
        :param username: The username credential.
        :param password: The user password component of credentials.
        :param dest_ip_address: The IP address of the node we want to connect to.
        :return: True if successful, False otherwise.
        """
        if self.operating_state != ServiceOperatingState.RUNNING:
            self.sys_log.warning("Cannot process login as service is not running")
            return False

        if ip_address:
            # if ip_address has been provided, we assume we are logging in to a remote terminal.
            return self._send_remote_login(username=username, password=password, ip_address=ip_address)

        return self._process_local_login(username=username, password=password)

    def _process_local_login(self, username: str, password: str) -> bool:
        """Local session login to terminal.

        :param username: Username for login.
        :param password: Password for login.
        :return: boolean, True if successful, else False
        """
        # TODO: Un-comment this when UserSessionManager is merged.
        # connection_uuid = self.parent.UserSessionManager.login(username=username, password=password)
        connection_uuid = str(uuid4())
        if connection_uuid:
            self.sys_log.info(f"Login request authorised, connection uuid: {connection_uuid}")
            # Add new local session to list of connections
            session_id = str(uuid4())
            self._add_new_connection(connection_uuid=connection_uuid, session_id=session_id)
            return True
        else:
            self.sys_log.warning("Login failed, incorrect Username or Password")
            return False

    def _send_remote_login(self, username: str, password: str, ip_address: IPv4Address) -> bool:
        """Attempt to login to a remote terminal.

        :param username: username for login.
        :param password: password for login.
        :ip_address: IP address of the target node for login.
        """
        transport_message: SSHTransportMessage = SSHTransportMessage.SSH_MSG_USERAUTH_REQUEST
        connection_message: SSHConnectionMessage = SSHConnectionMessage.SSH_MSG_CHANNEL_DATA
        user_account: SSHUserCredentials = SSHUserCredentials(username=username, password=password)

        payload: SSHPacket = SSHPacket(
            transport_message=transport_message,
            connection_message=connection_message,
            user_account=user_account,
        )

        self.sys_log.info(f"Sending remote login request to {ip_address}")
        return self.send(payload=payload, dest_ip_address=ip_address)

    def _process_remote_login(self, payload: SSHPacket, session_id: str) -> bool:
        """Processes a remote terminal requesting to login to this terminal.

        :param payload: The SSH Payload Packet.
        :param session_id: Session ID for sending login response.
        :return: True if successful, else False.
        """
        username: str = payload.user_account.username
        password: str = payload.user_account.password
        self.sys_log.info(f"Sending UserAuth request to UserSessionManager, username={username}, password={password}")
        # TODO: Un-comment this when UserSessionManager is merged.
        # connection_uuid = self.parent.UserSessionManager.remote_login(username=username, password=password)
        connection_uuid = str(uuid4())
        if connection_uuid:
            # Send uuid to remote
            self.sys_log.info(
                f"Remote login authorised, connection ID {connection_uuid} for " f"{username} in session {session_id}"
            )
            transport_message: SSHTransportMessage = SSHTransportMessage.SSH_MSG_USERAUTH_SUCCESS
            connection_message: SSHConnectionMessage = SSHConnectionMessage.SSH_MSG_CHANNEL_DATA
            return_payload = SSHPacket(
                transport_message=transport_message,
                connection_message=connection_message,
                connection_uuid=connection_uuid,
            )
            self._add_new_connection(connection_uuid=connection_uuid, session_id=session_id)

            self.send(payload=return_payload, session_id=session_id)
            return True
        else:
            # UserSessionManager has returned None
            self.sys_log.warning("Login failed, incorrect Username or Password")
            return False

    def receive(self, payload: SSHPacket, session_id: str, **kwargs) -> bool:
        """Receive Payload and process for a response.

        :param payload: The message contents received.
        :param session_id: Session ID of received message.
        :return: True if successful, else False.
        """
        self.sys_log.debug(f"Received payload: {payload}")

        if not isinstance(payload, SSHPacket):
            return False

        if self.operating_state != ServiceOperatingState.RUNNING:
            self.sys_log.warning("Cannot process message as not running")
            return False

        if payload.connection_message == SSHConnectionMessage.SSH_MSG_CHANNEL_CLOSE:
            # Close the channel
            connection_id = kwargs["connection_id"]
            dest_ip_address = kwargs["dest_ip_address"]
            self.disconnect(dest_ip_address=dest_ip_address)
            self.sys_log.debug(f"Disconnecting {connection_id}")

        elif payload.transport_message == SSHTransportMessage.SSH_MSG_USERAUTH_REQUEST:
            return self._process_remote_login(payload=payload, session_id=session_id)

        elif payload.transport_message == SSHTransportMessage.SSH_MSG_USERAUTH_SUCCESS:
            self.sys_log.info(f"Login Successful, connection ID is {payload.connection_uuid}")
            return True

        elif payload.transport_message == SSHTransportMessage.SSH_MSG_SERVICE_REQUEST:
            return self.execute(command=payload.payload)

        else:
            self.sys_log.warning("Encounter unexpected message type, rejecting connection")
            return False

        return True

    def execute(self, command: List[Any]) -> RequestResponse:
        """Execute a passed ssh command via the request manager."""
        return self.parent.apply_request(command)

    def _disconnect(self, connection_uuid: str) -> bool:
        """Disconnect from the remote.

        :param connection_uuid: Connection ID that we want to disconnect.
        :return True if successful, False otherwise.
        """
        if not self._connections:
            self.sys_log.warning("No remote connection present")
            return False

        dest_ip_address = self._connections[connection_uuid].dest_ip_address
        self._connections.pop(connection_uuid)

        software_manager: SoftwareManager = self.software_manager
        software_manager.send_payload_to_session_manager(
            payload={"type": "disconnect", "connection_id": connection_uuid},
            dest_ip_address=dest_ip_address,
            dest_port=self.port,
        )
        self.sys_log.info(f"{self.name}: Disconnected {connection_uuid}")
        return True

    def disconnect(self, connection_uuid: Optional[str]) -> bool:
        """Disconnect the terminal.

        If no connection id has been supplied, disconnects the first connection.
        :param connection_uuid: Connection ID that we want to disconnect.
        :return: True if successful, False otherwise.
        """
        if not connection_uuid:
            connection_uuid = next(iter(self._connections))

        return self._disconnect(connection_uuid=connection_uuid)

    def send(
        self, payload: SSHPacket, dest_ip_address: Optional[IPv4Address] = None, session_id: Optional[str] = None
    ) -> bool:
        """
        Send a payload out from the Terminal.

        :param payload: The payload to be sent.
        :param dest_up_address: The IP address of the payload destination.
        """
        if self.operating_state != ServiceOperatingState.RUNNING:
            self.sys_log.warning(f"Cannot send commands when Operating state is {self.operating_state}!")
            return False
        self.sys_log.debug(f"Sending payload: {payload}")
        return super().send(
            payload=payload, dest_ip_address=dest_ip_address, dest_port=self.port, session_id=session_id
        )
