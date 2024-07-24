# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from __future__ import annotations

from ipaddress import IPv4Address
from typing import Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel

from primaite.interface.request import RequestFormat, RequestResponse
from primaite.simulator.core import RequestManager, RequestPermissionValidator, RequestType
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


class TerminalClientConnection(BaseModel):
    """
    TerminalClientConnection Class.

    This class is used to record current remote User Connections to the Terminal class.
    """

    parent_node: Node  # Technically should be HostNode but this causes circular import error.
    """The parent Node that this connection was created on."""

    is_active: bool = True
    """Flag to state whether the connection is still active or not."""

    _dest_ip_address: IPv4Address
    """Destination IP address of connection"""

    _connection_uuid: str = None
    """Connection UUID"""

    @property
    def dest_ip_address(self) -> Optional[IPv4Address]:
        """Destination IP Address."""
        return self._dest_ip_address

    @property
    def client(self) -> Optional[Terminal]:
        """The Terminal that holds this connection."""
        return self.parent_node.software_manager.software.get("Terminal")

    def disconnect(self):
        """Disconnect the connection."""
        if self.client and self.is_active:
            self.client._disconnect(self._connection_uuid)  # noqa


class Terminal(Service):
    """Class used to simulate a generic terminal service. Can be interacted with by other terminals via SSH."""

    is_connected: bool = False
    "Boolean Value for whether connected"

    connection_uuid: Optional[str] = None
    "Uuid for connection requests"

    operating_state: ServiceOperatingState = ServiceOperatingState.RUNNING
    """Initial Operating State"""

    remote_connection: Dict[str, TerminalClientConnection] = {}

    def __init__(self, **kwargs):
        kwargs["name"] = "Terminal"
        kwargs["port"] = Port.SSH
        kwargs["protocol"] = IPProtocol.TCP
        super().__init__(**kwargs)

    # %% Util

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        Please see :py:meth:`primaite.simulator.core.SimComponent.describe_state` for a more detailed explanation.

        :return: Current state of this object and child objects.
        :rtype: Dict
        """
        state = super().describe_state()
        return state

    def apply_request(self, request: List[str | int | float | Dict], context: Dict | None = None) -> RequestResponse:
        """Apply Terminal Request."""
        return super().apply_request(request, context)

    def _init_request_manager(self) -> RequestManager:
        """Initialise Request manager."""
        _login_valid = Terminal._LoginValidator(terminal=self)

        rm = super()._init_request_manager()
        rm.add_request(
            "send",
            request_type=RequestType(
                func=lambda request, context: RequestResponse.from_bool(self.send()), validator=_login_valid
            ),
        )
        return rm

    def _validate_login(self) -> bool:
        """Validate login credentials are valid."""
        # return self.parent.UserSessionManager.validate_remote_session_uuid(self.connection_uuid)
        return True

    class _LoginValidator(RequestPermissionValidator):
        """
        When requests come in, this validator will only allow them through if the User is logged into the Terminal.

        Login is required before making use of the Terminal.
        """

        terminal: Terminal
        """Save a reference to the Terminal instance."""

        def __call__(self, request: RequestFormat, context: Dict) -> bool:
            """Return whether the Terminal is connected."""
            return self.terminal.is_connected

        @property
        def fail_message(self) -> str:
            """Message that is reported when a request is rejected by this validator."""
            return "Cannot perform request on terminal as not logged in."

    # %% Inbound

    def login(self, username: str, password: str, ip_address: Optional[IPv4Address] = None) -> bool:
        """Process User request to login to Terminal.

        :param dest_ip_address: The IP address of the node we want to connect to.
        :param username: The username credential.
        :param password: The user password component of credentials.
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
        """Local session login to terminal."""
        # self.connection_uuid = self.parent.UserSessionManager.login(username=username, password=password)
        self.connection_uuid = str(uuid4())
        if self.connection_uuid:
            self.sys_log.info(f"Login request authorised, connection uuid: {self.connection_uuid}")
            return True
        else:
            self.sys_log.warning("Login failed, incorrect Username or Password")
            return False

    def _send_remote_login(self, username: str, password: str, ip_address: IPv4Address) -> bool:
        """Attempt to login to a remote terminal."""
        transport_message: SSHTransportMessage = SSHTransportMessage.SSH_MSG_USERAUTH_REQUEST
        connection_message: SSHConnectionMessage = SSHConnectionMessage.SSH_MSG_CHANNEL_DATA
        user_account: SSHUserCredentials = SSHUserCredentials(username=username, password=password)

        payload: SSHPacket = SSHPacket(
            transport_message=transport_message,
            connection_message=connection_message,
            user_account=user_account,
            target_ip_address=ip_address,
            sender_ip_address=self.parent.network_interface[1].ip_address,
        )

        self.sys_log.info(f"Sending remote login request to {ip_address}")
        return self.send(payload=payload, dest_ip_address=ip_address)

    def _process_remote_login(self, payload: SSHPacket) -> bool:
        """Processes a remote terminal requesting to login to this terminal."""
        username: str = payload.user_account.username
        password: str = payload.user_account.password
        self.sys_log.info(f"Sending UserAuth request to UserSessionManager, username={username}, password={password}")
        # connection_uuid = self.parent.UserSessionManager.remote_login(username=username, password=password)
        connection_uuid = str(uuid4())

        if connection_uuid:
            # Send uuid to remote
            self.sys_log.info(
                f"Remote login authorised, connection ID {self.connection_uuid} for "
                f"{username} on {payload.sender_ip_address}"
            )
            transport_message: SSHTransportMessage = SSHTransportMessage.SSH_MSG_USERAUTH_SUCCESS
            connection_message: SSHConnectionMessage = SSHConnectionMessage.SSH_MSG_CHANNEL_DATA
            return_payload = SSHPacket(
                transport_message=transport_message,
                connection_message=connection_message,
                connection_uuid=connection_uuid,
                sender_ip_address=self.parent.network_interface[1].ip_address,
                target_ip_address=payload.sender_ip_address,
            )
            self.send(payload=return_payload, dest_ip_address=return_payload.target_ip_address)

            self.remote_connection[connection_uuid] = TerminalClientConnection(
                parent_node=self.software_manager.node,
                _dest_ip_address=payload.sender_ip_address,
                connection_uuid=connection_uuid,
            )

            return True
        else:
            # UserSessionManager has returned None
            self.sys_log.warning("Login failed, incorrect Username or Password")
            return False

    def receive(self, payload: SSHPacket, **kwargs) -> bool:
        """Receive Payload and process for a response."""
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
            # We need to close on the other machine as well

        elif payload.transport_message == SSHTransportMessage.SSH_MSG_USERAUTH_REQUEST:
            """Login Request Received."""
            self._process_remote_login(payload=payload)

        elif payload.transport_message == SSHTransportMessage.SSH_MSG_USERAUTH_SUCCESS:
            self.sys_log.info(f"Login Successful, connection ID is {payload.connection_uuid}")
            self.connection_uuid = payload.connection_uuid
            self.is_connected = True
            return True

        else:
            self.sys_log.warning("Encounter unexpected message type, rejecting connection")
            return False

        return True

    # %% Outbound

    def _disconnect(self, dest_ip_address: IPv4Address) -> bool:
        """Disconnect from the remote."""
        if not self.is_connected:
            self.sys_log.warning("Not currently connected to remote")
            return False

        if not self.remote_connection:
            self.sys_log.warning("No remote connection present")
            return False

        software_manager: SoftwareManager = self.software_manager
        software_manager.send_payload_to_session_manager(
            payload={"type": "disconnect", "connection_id": self.remote_connection._connection_uuid},
            dest_ip_address=dest_ip_address,
            dest_port=self.port,
        )
        self.connection_uuid = None
        self.sys_log.info(f"{self.name}: Disconnected {self.connection_uuid}")
        return True

    def disconnect(self, dest_ip_address: IPv4Address) -> bool:
        """Disconnect from remote connection.

        :param dest_ip_address: The IP address fo the connection we are terminating.
        :return: True if successful, False otherwise.
        """
        self._disconnect(dest_ip_address=dest_ip_address)
        self.is_connected = False

    def send(
        self,
        payload: SSHPacket,
        dest_ip_address: IPv4Address,
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
        return super().send(payload=payload, dest_ip_address=dest_ip_address, dest_port=self.port)
