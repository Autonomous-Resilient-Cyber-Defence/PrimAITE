# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from __future__ import annotations

from ipaddress import IPv4Address
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel

from primaite.interface.request import RequestResponse
from primaite.simulator.core import RequestManager
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

    connection_id: str
    """Connection UUID."""

    parent_node: Node   # Technically I think this should be HostNode, but that causes a circular import.
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
        rm = super()._init_request_manager()
        return rm

    # %% Inbound

    def _generate_connection_id(self) -> str:
        """Generate a unique connection ID."""
        return str(uuid4())

    def process_login(self, dest_ip_address: IPv4Address, user_account: dict, **kwargs) -> bool:
        """Process User request to login to Terminal."""
        if user_account in self.user_connections:
            self.sys_log.debug("User authentication passed")
            return True
        else:
            self._ssh_process_login(dest_ip_address=dest_ip_address, user_account=user_account)
            self.process_login(dest_ip_address=dest_ip_address, user_account=user_account)

    def _ssh_process_login(self, dest_ip_address: IPv4Address, user_account: dict, **kwargs) -> bool:
        """Processes the login attempt. Returns a bool which either rejects the login or accepts it."""
        # we assume that the login fails unless we meet all the criteria.
        transport_message = SSHTransportMessage.SSH_MSG_USERAUTH_FAILURE
        connection_message = SSHConnectionMessage.SSH_MSG_CHANNEL_OPEN_FAILED

        # Hard coded at current - replace with another method to handle local accounts.
        if user_account == f"{self.user_name:} placeholder, {self.password:} placeholder":  # hardcoded
            connection_id = self._generate_connection_id()
            if not self.add_connection(self, connection_id=connection_id):
                self.sys_log.warning(
                    f"{self.name}: Connect request for {dest_ip_address} declined. Service is at capacity."
                )
                return False
            else:
                self.sys_log.info(f"{self.name}: Connect request for ID: {connection_id} authorised")
                transport_message = SSHTransportMessage.SSH_MSG_USERAUTH_SUCCESS
                connection_message = SSHConnectionMessage.SSH_MSG_CHANNEL_OPEN_CONFIRMATION
                new_connection = TerminalClientConnection(connection_id=connection_id, dest_ip_address=dest_ip_address)
                self.user_connections[connection_id] = new_connection
                self.is_connected = True

        payload: SSHPacket = SSHPacket(transport_message=transport_message, connection_message=connection_message)

        self.send(payload=payload, dest_ip_address=dest_ip_address)
        return True

    def validate_user(self, user: Dict[str]) -> bool:
        return True if user.get("username") in self.user_connections else False


    def _ssh_process_logoff(self, dest_ip_address: IPv4Address, user_account: dict, **kwargs) -> bool:
        """Process the logoff attempt. Return a bool if succesful or unsuccessful."""
        
        if self.validate_user(user_account):
            # Account is logged in
            self.user_connections.pop[user_account["username"]] # assumption atm
            self.is_connected = False
            return True
        else:
            self.sys_log.warning("User account credentials invalid.")

    def _ssh_process_command(self, session_id: str, *args, **kwargs) -> bool:
        return True

    def send_logoff_ack(self):
        """Send confirmation of successful disconnect"""
        transport_message = SSHTransportMessage.SSH_MSG_SERVICE_SUCCESS
        connection_message = SSHConnectionMessage.SSH_MSG_CHANNEL_CLOSE
        payload: SSHPacket = SSHPacket(transport_message=transport_message, connection_message=connection_message, ssh_output=RequestResponse(status="success"))
        self.send(payload=payload)

    def receive(self, payload: SSHPacket, session_id: str, **kwargs) -> bool:
            self.sys_log.debug(f"Received payload: {payload} from session: {session_id}")
            if payload.connection_message ==SSHConnectionMessage. SSH_MSG_CHANNEL_CLOSE:
                result = self._ssh_process_logoff(session_id=session_id)  
                # We need to close on the other machine as well
                self.send_logoff_ack()

            elif payload.transport_message == SSHTransportMessage.SSH_MSG_USERAUTH_REQUEST:
                src_ip = kwargs.get("frame").ip.src_ip_address
                user_account = payload.get("user_account", {})
                result = self._ssh_process_login(src_ip=src_ip, session_id=session_id, user_account=user_account)

            elif payload.transport_message == SSHTransportMessage.SSH_MSG_SERVICE_REQUEST:
                # Ensure we only ever process requests if we have a established connection (e.g session_id is provided and validated)
                result = self._ssh_process_command(session_id=session_id)

            else:
                self.sys_log.warning("Encounter unexpected message type, rejecting connection")
                # send a SSH_MSG_CHANNEL_CLOSE if there is a session_id otherwise SSH_MSG_OPEN_FAILED
                return False

            self.send(payload=result, session_id=session_id)
            return True


    # %% Outbound

    def login(self, dest_ip_address: IPv4Address) -> bool:
        """
        Perform an initial login request.

        If this fails, raises an error.
        """
        # TODO: This will need elaborating when user accounts are implemented
        self.sys_log.info("Attempting Login")
        return self.ssh_remote_login(self, dest_ip_address=dest_ip_address, user_account=self.user_account)

    def ssh_remote_login(self, dest_ip_address: IPv4Address, user_account: Optional[dict] = None) -> bool:
        """Remote login to terminal via SSH."""
        if not user_account:
            # Setting default creds (Best to use this until we have more clarification around user accounts)
            user_account = {self.user_name: "placeholder", self.password: "placeholder"}

        # Implement SSHPacket class
        payload: SSHPacket = SSHPacket(
            transport_message=SSHTransportMessage.SSH_MSG_USERAUTH_REQUEST,
            connection_message=SSHConnectionMessage.SSH_MSG_CHANNEL_OPEN,
            user_account=user_account,
        )
        # self.send will return bool, payload unchanged?
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

    def disconnect(self, connection_id: str):
        """Disconnect from remote."""
        self._disconnect(connection_id)
        self.is_connected = False

    def _disconnect(self, connection_id: str) -> bool:
        if not self.is_connected:
            return False

        if len(self.user_connections) == 0:
            self.sys_log.warning(f"{self.name}: Unable to disconnect, no active connections.")
            return False
        if not self.user_connections.get(connection_id):
            return False
        software_manager: SoftwareManager = self.software_manager
        software_manager.send_payload_to_session_manager(
            payload={"type": "disconnect", "connection_id": connection_id},
            dest_ip_address=self.server_ip_address,
            dest_port=self.port,
        )
        connection = self.user_connections.pop(connection_id)
        self.terminate_connection(connection_id=connection_id)

        connection.is_active = False

        self.sys_log.info(
            f"{self.name}: Disconnected {connection_id} from: {self.user_connections[connection_id]._dest_ip_address}"
        )
        self.connected = False
        return True


    def send(
            self,
            payload: SSHPacket,
            dest_ip_address: Optional[IPv4Address] = None,
            session_id: Optional[str] = None,
        ) -> bool:
            return super().send(payload=payload, dest_ip_address=dest_ip_address, dest_port=Port.SSH, session_id=session_id)

