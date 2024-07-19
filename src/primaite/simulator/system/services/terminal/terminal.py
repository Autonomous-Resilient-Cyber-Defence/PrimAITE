# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from __future__ import annotations

from ipaddress import IPv4Address
from typing import Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel

from primaite.interface.request import RequestFormat, RequestResponse
from primaite.simulator.core import RequestManager, RequestPermissionValidator, RequestType
from primaite.simulator.network.hardware.base import Node
from primaite.simulator.network.protocols.ssh import SSHConnectionMessage, SSHPacket, SSHTransportMessage
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.core.software_manager import SoftwareManager
from primaite.simulator.system.services.service import Service, ServiceOperatingState


class TerminalClientConnection(BaseModel):
    """
    TerminalClientConnection Class.

    This class is used to record current User Connections within the Terminal class.
    """

    parent_node: Node  # Technically I think this should be HostNode, but that causes a circular import.
    """The parent Node that this connection was created on."""

    is_active: bool = True
    """Flag to state whether the connection is still active or not."""

    _dest_ip_address: IPv4Address
    """Destination IP address of connection"""

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
            self.client._disconnect(self.connection_id)  # noqa


class Terminal(Service):
    """Class used to simulate a generic terminal service. Can be interacted with by other terminals via SSH."""

    user_account: Optional[str] = None
    "The User Account used for login"

    is_connected: bool = False
    "Boolean Value for whether connected"

    connection_uuid: Optional[str] = None
    "Uuid for connection requests"

    operating_state: ServiceOperatingState = ServiceOperatingState.RUNNING
    """Initial Operating State"""

    user_connections: Dict[str, TerminalClientConnection] = {}
    """List of authenticated connected users"""

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

        state.update({"hostname": self.name})
        return state

    def apply_request(self, request: List[str | int | float | Dict], context: Dict | None = None) -> RequestResponse:
        """Apply Temrinal Request."""
        return super().apply_request(request, context)

    def _init_request_manager(self) -> RequestManager:
        """Initialise Request manager."""
        # TODO: Expand with a login validator?

        _login_valid = Terminal._LoginValidator(terminal=self)

        rm = super()._init_request_manager()
        rm.add_request("login", request_type=RequestType(func=lambda request, context: RequestResponse.from_bool(self._validate_login()), validator=_login_valid))
        return rm

    def _validate_login(self, user_account: Optional[str]) -> bool:
        """Validate login credentials are valid."""
        # TODO: Interact with UserManager to check user_account details
        if len(self.user_connections) == 0:
            # No current connections
            self.sys_log.warning("Login Required!")
            return False
        else:
            return True

    class _LoginValidator(RequestPermissionValidator):
        """
        When requests come in, this validator will only allow them through if the
        User is logged into the Terminal.

        Login is required before making use of the Terminal.
        """

        terminal: Terminal
        """Save a reference to the Terminal instance."""

        def __call__(self, request: RequestFormat, context: Dict) -> bool:
            """Return whether the Terminal has valid login credentials"""
            return self.terminal.login_status
        
        @property
        def fail_message(self) -> str:
            """Message that is reported when a request is rejected by this validator"""
            return ("Cannot perform request on terminal as not logged in.")


    # %% Inbound

    def _generate_connection_uuid(self) -> str:
        """Generate a unique connection ID."""
        # This might not be needed given user_manager.login() returns a UUID.
        return str(uuid4())

    def login(self, dest_ip_address: IPv4Address, **kwargs) -> bool:
        """Process User request to login to Terminal.

        :param dest_ip_address: The IP address of the node we want to connect to.
        :return: True if successful, False otherwise.
        """
        if self.operating_state != ServiceOperatingState.RUNNING:
            self.sys_log.warning("Cannot process login as service is not running")
            return False
        if self.connection_uuid in self.user_connections:
            self.sys_log.debug("User authentication passed")
            return True
        else:
            # Need to send a login request
            # TODO: Refactor with UserManager changes to provide correct credentials and validate.
            transport_message = SSHTransportMessage.SSH_MSG_USERAUTH_REQUEST
            connection_message = SSHConnectionMessage.SSH_MSG_CHANNEL_OPEN
            payload: SSHPacket = SSHPacket(
                payload="login", transport_message=transport_message, connection_message=connection_message
            )

            self.sys_log.info(f"Sending login request to {dest_ip_address}")
            self.send(payload=payload, dest_ip_address=dest_ip_address)

    def _ssh_process_login(self, dest_ip_address: IPv4Address, user_account: dict, **kwargs) -> bool:
        """Processes the login attempt. Returns a bool which either rejects the login or accepts it."""
        # we assume that the login fails unless we meet all the criteria.
        transport_message = SSHTransportMessage.SSH_MSG_USERAUTH_FAILURE
        connection_message = SSHConnectionMessage.SSH_MSG_CHANNEL_OPEN_FAILED

        # Hard coded at current - replace with another method to handle local accounts.
        if user_account == "Username: placeholder, Password: placeholder":  # hardcoded
            self.connection_uuid = self._generate_connection_uuid()
            if not self.add_connection(connection_id=self.connection_uuid):
                self.sys_log.warning(
                    f"{self.name}: Connect request for {dest_ip_address} declined. Service is at capacity."
                )
                return False
            else:
                self.sys_log.info(f"{self.name}: Connect request for ID: {self.connection_uuid} authorised")
                transport_message = SSHTransportMessage.SSH_MSG_USERAUTH_SUCCESS
                connection_message = SSHConnectionMessage.SSH_MSG_CHANNEL_OPEN_CONFIRMATION
                new_connection = TerminalClientConnection(
                    parent_node=self.software_manager.node,
                    connection_id=self.connection_uuid,
                    dest_ip_address=dest_ip_address,
                )
                self.user_connections[self.connection_uuid] = new_connection
                self.is_connected = True

        payload: SSHPacket = SSHPacket(transport_message=transport_message, connection_message=connection_message)

        self.send(payload=payload, dest_ip_address=dest_ip_address)
        return True

    def _ssh_process_logoff(self, session_id: str, *args, **kwargs) -> bool:
        """Process the logoff attempt. Return a bool if succesful or unsuccessful."""
        # TODO: Should remove

    def receive(self, payload: SSHPacket, session_id: str, **kwargs) -> bool:
        """Receive Payload and process for a response."""
        if not isinstance(payload, SSHPacket):
            return False

        if self.operating_state != ServiceOperatingState.RUNNING:
            self.sys_log.warning("Cannot process message as not running")
            return False

        self.sys_log.debug(f"Received payload: {payload} from session: {session_id}")

        if payload.connection_message == SSHConnectionMessage.SSH_MSG_CHANNEL_CLOSE:
            connection_id = kwargs["connection_id"]
            dest_ip_address = kwargs["dest_ip_address"]
            self._ssh_process_logoff(session_id=session_id)
            self.disconnect(dest_ip_address=dest_ip_address)
            self.sys_log.debug(f"Disconnecting {connection_id}")
            # We need to close on the other machine as well

        elif payload.transport_message == SSHTransportMessage.SSH_MSG_USERAUTH_REQUEST:
            # validate login
            user_account = "Username: placeholder, Password: placeholder"
            self._ssh_process_login(dest_ip_address="192.168.0.10", user_account=user_account)

        elif payload.transport_message == SSHTransportMessage.SSH_MSG_USERAUTH_SUCCESS:
            self.sys_log.debug("Login Successful")
            self.is_connected = True
            return True

        else:
            self.sys_log.warning("Encounter unexpected message type, rejecting connection")
            return False

        return True

    # %% Outbound
    def _ssh_remote_login(self, dest_ip_address: IPv4Address, user_account: Optional[dict] = None) -> bool:
        """Remote login to terminal via SSH."""
        if not user_account:
            # TODO: Generic hardcoded info, will need to be updated with UserManager.
            user_account = "Username: placeholder, Password: placeholder"
            # something like self.user_manager.get_user_details ?

        # Implement SSHPacket class
        payload: SSHPacket = SSHPacket(
            transport_message=SSHTransportMessage.SSH_MSG_USERAUTH_REQUEST,
            connection_message=SSHConnectionMessage.SSH_MSG_CHANNEL_OPEN,
            user_account=user_account,
        )
        if self.send(payload=payload, dest_ip_address=dest_ip_address):
            if payload.connection_message == SSHTransportMessage.SSH_MSG_USERAUTH_SUCCESS:
                self.sys_log.info(f"{self.name} established an ssh connection with {dest_ip_address}")
                # Need to confirm if self.uuid is correct.
                self.add_connection(self, connection_id=self.uuid, session_id=self.session_id)
                return True
            else:
                self.sys_log.error("Login Failed. Incorrect credentials provided.")
                return False
        else:
            self.sys_log.error("Login Failed. Incorrect credentials provided.")
            return False

    def check_connection(self, connection_id: str) -> bool:
        """Check whether the connection is valid."""
        if self.is_connected:
            return self.send(dest_ip_address=self.dest_ip_address, connection_id=connection_id)
        else:
            return False

    def disconnect(self, dest_ip_address: IPv4Address) -> bool:
        """Disconnect from remote connection.

        :param dest_ip_address: The IP address fo the connection we are terminating.
        :return: True if successful, False otherwise.
        """
        self._disconnect(dest_ip_address=dest_ip_address)
        self.is_connected = False

    def _disconnect(self, dest_ip_address: IPv4Address) -> bool:
        if not self.is_connected:
            return False

        if len(self.user_connections) == 0:
            self.sys_log.warning(f"{self.name}: Unable to disconnect, no active connections.")
            return False
        if not self.user_connections.get(self.connection_uuid):
            return False
        software_manager: SoftwareManager = self.software_manager
        software_manager.send_payload_to_session_manager(
            payload={"type": "disconnect", "connection_id": self.connection_uuid},
            dest_ip_address=dest_ip_address,
            dest_port=self.port,
        )
        connection = self.user_connections.pop(self.connection_uuid)

        connection.is_active = False

        self.sys_log.info(f"{self.name}: Disconnected {self.connection_uuid}")
        return True

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
