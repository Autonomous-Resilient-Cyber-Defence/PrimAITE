# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from __future__ import annotations

from ipaddress import IPv4Address
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from prettytable import MARKDOWN, PrettyTable
from pydantic import BaseModel

from primaite.interface.request import RequestFormat, RequestResponse
from primaite.simulator.core import RequestManager, RequestType
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


class TerminalClientConnection(BaseModel):
    """
    TerminalClientConnection Class.

    This class is used to record current User Connections to the Terminal class.
    """

    parent_terminal: Terminal
    """The parent Node that this connection was created on."""

    session_id: str = None
    """Session ID that connection is linked to"""

    connection_uuid: str = None
    """Connection UUID"""

    connection_request_id: str = None
    """Connection request ID"""

    @property
    def client(self) -> Optional[Terminal]:
        """The Terminal that holds this connection."""
        return self.parent_terminal

    def disconnect(self) -> bool:
        """Disconnect the session."""
        return self.parent_terminal._disconnect(connection_uuid=self.connection_uuid)


class RemoteTerminalConnection(TerminalClientConnection):
    """
    RemoteTerminalConnection Class.

    This class acts as broker between the terminal and remote.

    """

    source_ip: IPv4Address
    """Source IP of Connection"""

    def execute(self, command: Any) -> bool:
        """Execute a given command on the remote Terminal."""
        if self.parent_terminal.operating_state != ServiceOperatingState.RUNNING:
            self.parent_terminal.sys_log.warning("Cannot process command as system not running")
        # Send command to remote terminal to process.
        return self.parent_terminal.send(payload=command, session_id=self.session_id)


class Terminal(Service):
    """Class used to simulate a generic terminal service. Can be interacted with by other terminals via SSH."""

    _client_connection_requests: Dict[str, Optional[str]] = {}

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
        table = PrettyTable(["Connection ID", "Connection request ID", "Source IP"])
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.sys_log.hostname} {self.name} Connections"
        for connection_id, connection in self._connections.items():
            table.add_row([connection_id, connection.connection_request_id, connection.source_ip])
        print(table.get_string(sortby="Connection ID"))

    def _init_request_manager(self) -> RequestManager:
        """Initialise Request manager."""
        rm = super()._init_request_manager()
        rm.add_request(
            "send",
            request_type=RequestType(func=lambda request, context: RequestResponse.from_bool(self.send())),
        )

        def _login(request: RequestFormat, context: Dict) -> RequestResponse:
            login = self._process_local_login(username=request[0], password=request[1])
            if login:
                return RequestResponse(status="success", data={})
            else:
                return RequestResponse(status="failure", data={})

        def _remote_login(request: RequestFormat, context: Dict) -> RequestResponse:
            login = self._send_remote_login(username=request[0], password=request[1], ip_address=request[2])
            if login:
                return RequestResponse(status="success", data={})
            else:
                return RequestResponse(status="failure", data={})

        def _execute_request(request: RequestFormat, context: Dict) -> RequestResponse:
            """Execute an instruction."""
            command: str = request[0]
            self.execute(command)
            return RequestResponse(status="success", data={})

        def _logoff(request: RequestFormat, context: Dict) -> RequestResponse:
            """Logoff from connection."""
            connection_uuid = request[0]
            # TODO: Uncomment this when UserSessionManager merged.
            # self.parent.UserSessionManager.logoff(connection_uuid)
            self._disconnect(connection_uuid)

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

    def execute(self, command: List[Any]) -> RequestResponse:
        """Execute a passed ssh command via the request manager."""
        return self.parent.apply_request(command)

    def _create_local_connection(self, connection_uuid: str, session_id: str) -> TerminalClientConnection:
        """Create a new connection object and amend to list of active connections.

        :param connection_uuid: Connection ID of the new local connection
        :param session_id: Session ID of the new local connection
        :return: TerminalClientConnection object
        """
        new_connection = TerminalClientConnection(
            parent_terminal=self,
            connection_uuid=connection_uuid,
            session_id=session_id,
        )
        self._connections[connection_uuid] = new_connection
        self._client_connection_requests[connection_uuid] = new_connection

        return new_connection

    def login(
        self, username: str, password: str, ip_address: Optional[IPv4Address] = None
    ) -> Optional[TerminalClientConnection]:
        """Login to the terminal. Will attempt a remote login if ip_address is given, else local.

        :param: username: Username used to connect to the remote node.
        :type: username: str

        :param: password: Password used to connect to the remote node
        :type: password: str

        :param: ip_address: Target Node IP address for login attempt. If None, login is assumed local.
        :type: ip_address: Optional[IPv4Address]
        """
        if self.operating_state != ServiceOperatingState.RUNNING:
            self.sys_log.warning("Cannot login as service is not running.")
            return None
        connection_request_id = str(uuid4())
        self._client_connection_requests[connection_request_id] = None
        if ip_address:
            # Assuming that if IP is passed we are connecting to remote
            return self._send_remote_login(
                username=username, password=password, ip_address=ip_address, connection_request_id=connection_request_id
            )
        else:
            return self._process_local_login(username=username, password=password)

    def _process_local_login(self, username: str, password: str) -> Optional[TerminalClientConnection]:
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
            self._create_local_connection(connection_uuid=connection_uuid, session_id="Local_Connection")
            return TerminalClientConnection(
                parent_terminal=self, session_id="Local_Connection", connection_uuid=connection_uuid
            )
        else:
            self.sys_log.warning("Login failed, incorrect Username or Password")
            return None

    def _check_client_connection(self, connection_id: str) -> bool:
        """Check that client_connection_id is valid."""
        return True if connection_id in self._client_connection_requests else False

    def _send_remote_login(
        self,
        username: str,
        password: str,
        ip_address: IPv4Address,
        connection_request_id: str,
        is_reattempt: bool = False,
    ) -> Optional[RemoteTerminalConnection]:
        """Send a remote login attempt and connect to Node.

        :param: username: Username used to connect to the remote node.
        :type: username: str

        :param: password: Password used to connect to the remote node
        :type: password: str

        :param: ip_address: Target Node IP address for login attempt.
        :type: ip_address: IPv4Address

        :param: connection_request_id: Connection Request ID
        :type: connection_request_id: str

        :param: is_reattempt: True if the request has been reattempted. Default False.
        :type: is_reattempt: Optional[bool]

        :return: RemoteTerminalConnection: Connection Object for sending further commands if successful, else False.

        """
        self.sys_log.info(f"Sending Remote login attempt to {ip_address}. Connection_id is {connection_request_id}")
        if is_reattempt:
            valid_connection = self._check_client_connection(connection_id=connection_request_id)
            if valid_connection:
                remote_terminal_connection = self._client_connection_requests.pop(connection_request_id)
                self.sys_log.info(f"{self.name}: Remote Connection to {ip_address} authorised.")
                return remote_terminal_connection
            else:
                self.sys_log.warning(f"{self.name}: Remote connection to {ip_address} declined.")
                return None

        transport_message: SSHTransportMessage = SSHTransportMessage.SSH_MSG_USERAUTH_REQUEST
        connection_message: SSHConnectionMessage = SSHConnectionMessage.SSH_MSG_CHANNEL_DATA
        user_details: SSHUserCredentials = SSHUserCredentials(username=username, password=password)

        payload_contents = {
            "type": "login_request",
            "username": username,
            "password": password,
            "connection_request_id": connection_request_id,
        }

        payload: SSHPacket = SSHPacket(
            payload=payload_contents,
            transport_message=transport_message,
            connection_message=connection_message,
            user_account=user_details,
            connection_request_uuid=connection_request_id,
        )

        software_manager: SoftwareManager = self.software_manager
        software_manager.send_payload_to_session_manager(
            payload=payload, dest_ip_address=ip_address, dest_port=self.port
        )
        return self._send_remote_login(
            username=username,
            password=password,
            ip_address=ip_address,
            is_reattempt=True,
            connection_request_id=connection_request_id,
        )

    def _create_remote_connection(
        self, connection_id: str, connection_request_id: str, session_id: str, source_ip: str
    ) -> None:
        """Create a new TerminalClientConnection Object.

        :param: connection_request_id: Connection Request ID
        :type: connection_request_id: str

        :param: session_id: Session ID of connection.
        :type: session_id: str
        """
        client_connection = RemoteTerminalConnection(
            parent_terminal=self,
            session_id=session_id,
            connection_uuid=connection_id,
            source_ip=source_ip,
            connection_request_id=connection_request_id,
        )
        self._connections[connection_id] = client_connection
        self._client_connection_requests[connection_request_id] = client_connection

    def receive(self, session_id: str, payload: Union[SSHPacket, Dict, List], **kwargs) -> bool:
        """
        Receive a payload from the Software Manager.

        :param payload: A payload to receive.
        :param session_id: The session id the payload relates to.
        :return: True.
        """
        source_ip = kwargs["from_network_interface"].ip_address
        self.sys_log.info(f"Received payload: {payload}. Source: {source_ip}")
        if isinstance(payload, SSHPacket):
            if payload.transport_message == SSHTransportMessage.SSH_MSG_USERAUTH_REQUEST:
                # validate & add connection
                # TODO: uncomment this as part of 2781
                # connection_id = self.parent.UserSessionManager.login(username=username, password=password)
                connection_id = str(uuid4())
                if connection_id:
                    connection_request_id = payload.connection_request_uuid
                    username = payload.user_account.username
                    password = payload.user_account.password
                    print(f"Connection ID is: {connection_request_id}")
                    self.sys_log.info(f"Connection authorised, session_id: {session_id}")
                    self._create_remote_connection(
                        connection_id=connection_id,
                        connection_request_id=connection_request_id,
                        session_id=session_id,
                        source_ip=source_ip,
                    )

                    transport_message = SSHTransportMessage.SSH_MSG_USERAUTH_SUCCESS
                    connection_message = SSHConnectionMessage.SSH_MSG_CHANNEL_DATA

                    payload_contents = {
                        "type": "login_success",
                        "username": username,
                        "password": password,
                        "connection_request_id": connection_request_id,
                        "connection_id": connection_id,
                    }
                    payload: SSHPacket = SSHPacket(
                        payload=payload_contents,
                        transport_message=transport_message,
                        connection_message=connection_message,
                        connection_request_uuid=connection_request_id,
                        connection_uuid=connection_id,
                    )

                    software_manager: SoftwareManager = self.software_manager
                    software_manager.send_payload_to_session_manager(
                        payload=payload, dest_port=self.port, session_id=session_id
                    )
            elif payload.transport_message == SSHTransportMessage.SSH_MSG_USERAUTH_SUCCESS:
                self.sys_log.info("Login Successful")
                self._create_remote_connection(
                    connection_id=payload.connection_uuid,
                    connection_request_id=payload.connection_request_uuid,
                    session_id=session_id,
                    source_ip=source_ip,
                )

        if isinstance(payload, dict) and payload.get("type"):
            if payload["type"] == "disconnect":
                connection_id = payload["connection_id"]
                self.sys_log.info(f"{self.name}: Received disconnect command for {connection_id=} from remote.")
                self._disconnect(payload["connection_id"])

        if isinstance(payload, list):
            # A request? For me?
            self.execute(payload)

        return True

    def _disconnect(self, connection_uuid: str) -> bool:
        """Disconnect from the remote.

        :param connection_uuid: Connection ID that we want to disconnect.
        :return True if successful, False otherwise.
        """
        if not self._connections:
            self.sys_log.warning("No remote connection present")
            return False

        session_id = self._connections[connection_uuid].session_id
        self._connections.pop(connection_uuid)

        software_manager: SoftwareManager = self.software_manager
        software_manager.send_payload_to_session_manager(
            payload={"type": "disconnect", "connection_id": connection_uuid}, dest_port=self.port, session_id=session_id
        )
        self.sys_log.info(f"{self.name}: Disconnected {connection_uuid}")
        return True

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
