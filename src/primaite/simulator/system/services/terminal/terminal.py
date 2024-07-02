# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from __future__ import annotations

from ipaddress import IPv4Address, IPv4Network
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from primaite.interface.request import RequestFormat, RequestResponse
from primaite.simulator.core import RequestManager, RequestPermissionValidator
from primaite.simulator.network.protocols.icmp import ICMPPacket

# from primaite.simulator.network.protocols.ssh import SSHPacket, SSHTransportMessage, SSHConnectionMessage
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.services.service import Service, ServiceOperatingState


class Terminal(Service):
    """Class used to simulate a generic terminal service. Can be interacted with by other terminals via SSH."""

    user_account: Optional[str] = None
    "The User Account used for login"

    connected: bool = False
    "Boolean Value for whether connected"

    connection_uuid: Optional[str] = None
    "Uuid for connection requests"

    def __init__(self, **kwargs):
        kwargs["name"] = "Terminal"
        kwargs["port"] = Port.SSH
        kwargs["protocol"] = IPProtocol.TCP

        super().__init__(**kwargs)
        self.operating_state = ServiceOperatingState.RUNNING

    class _LoginValidator(RequestPermissionValidator):
        """
        When requests come in, this validator will only let them through if we have valid login credentials.

        This should ensure that no actions are resolved without valid user credentials.
        """

        terminal: Terminal

        def __call__(self, request: RequestFormat, context: Dict) -> bool:
            """Return whether the login credentials are valid."""
            pass

        @property
        def fail_message(self) -> str:
            """Message that is reported when a request is rejected by this validator."""
            return (
                f"Cannot perform request on Terminal '{self.terminal.hostname}' because login credentials are invalid"
            )

    def _validate_login(self) -> bool:
        """Validate login credentials when receiving commands."""
        # TODO: Implement
        return True

    def receive_payload_from_software_manager(
        self,
        payload: Any,
        dst_ip_address: Optional[Union[IPv4Address, IPv4Network]] = None,
        src_port: Optional[Port] = None,
        dst_port: Optional[Port] = None,
        session_id: Optional[str] = None,
        ip_protocol: IPProtocol = IPProtocol.TCP,
        icmp_packet: Optional[ICMPPacket] = None,
        connection_id: Optional[str] = None,
    ) -> Union[Any, None]:
        """Receive Software Manager Payload."""
        self._validate_login()

    def _init_request_manager(self) -> RequestManager:
        """Initialise Request manager."""
        # _login_is_valid = Terminal._LoginValidator(terminal=self)
        rm = super()._init_request_manager()

        return rm

    def send(
        self,
        payload: Any,
        dest_ip_address: Optional[IPv4Address] = None,
        session_id: Optional[str] = None,
    ) -> bool:
        """Send Request to Software Manager."""
        return super().send(payload=payload, dest_ip_address=dest_ip_address, dest_port=Port.SSH, session_id=session_id)

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        Please see :py:meth:`primaite.simulator.core.SimComponent.describe_state` for a more detailed explanation.

        :return: Current state of this object and child objects.
        :rtype: Dict
        """
        state = super().describe_state()
        # TBD
        state.update({"hostname": self.hostname})
        return state

    def execute(self, command: Any, request: Any) -> Optional[RequestResponse]:
        """Execute Command."""
        #  Returning the request to the request manager.
        if self._validate_login():
            return self.apply_request(request)
        else:
            self.sys_log.error("Invalid login credentials provided.")
            return None

    def apply_request(self, request: List[str | int | float | Dict], context: Dict | None = None) -> RequestResponse:
        """Apply Temrinal Request."""
        return super().apply_request(request, context)

    def login(self, dest_ip_address: IPv4Address) -> bool:
        """
        Perform an initial login request.

        If this fails, raises an error.
        """
        # TODO: This will need elaborating when user accounts are implemented
        self.sys_log.info("Attempting Login")
        self._ssh_process_login(self, dest_ip_address=dest_ip_address, user_account=self.user_account)

    def _generate_connection_id(self) -> str:
        """Generate a unique connection ID."""
        return str(uuid4())

    # %%

    # def _ssh_process_login(self, user_account: dict, **kwargs) -> SSHPacket:
    #     """Processes the login attempt. Returns a SSHPacket which either rejects the login or accepts it."""
    #     # we assume that the login fails unless we meet all the criteria.
    #     transport_message = SSHTransportMessage.SSH_MSG_USERAUTH_FAILURE
    #     connection_message = SSHConnectionMessage.SSH_MSG_CHANNEL_OPEN_FAILED
    #     # operating state validation here(if overwhelmed)

    #     # Hard coded at current - replace with another method to handle local accounts.
    #     if user_account == f"{self.user_name:} placeholder, {self.password:} placeholder": # hardcoded
    #             connection_id = self._generate_connection_id()
    #             if not self.add_connection(self, connection_id="ssh_connection", session_id=self.session_id):
    #                 self.sys_log.warning(f"{self.name}: Connect request for {self.src_ip} declined.
    #                                       Service is at capacity.")
    #                 ...
    #             else:
    #                 self.sys_log.info(f"{self.name}: Connect request for {connection_id=} authorised")
    #                 transport_message = SSHTransportMessage.SSH_MSG_USERAUTH_SUCCESS
    #                 connection_message = SSHConnectionMessage.SSH_MSG_CHANNEL_OPEN_CONFIRMATION

    #     payload: SSHPacket = SSHPacket(transport_message = transport_message, connection_message = connection_message)
    #     return payload

    # %%
    # Copy + Paste from Terminal Wiki

    # def ssh_remote_login(self, dest_ip_address = IPv4Address, user_account: Optional[dict] = None) -> bool:
    #     if user_account:
    #     # Setting default creds (Best to use this until we have more clarification on the specifics of user accounts)
    #             self.user_account = {self.user_name:"placeholder", self.password:"placeholder"}

    #     # Implement SSHPacket class
    #     payload: SSHPacket = SSHPacket(transport_message= SSHTransportMessage.SSH_MSG_USERAUTH_REQUEST,
    #                                    connection_message= SSHConnectionMessage.SSH_MSG_CHANNEL_OPEN,
    #                                    user_account=user_account)
    #     if self.send(payload=payload,dest_ip_address=dest_ip_address):
    #         if payload.connection_message == SSHTransportMessage.SSH_MSG_USERAUTH_SUCCESS:
    #             self.sys_log.info(f"{self.name} established an ssh connection with {dest_ip_address}")
    #             # Need to confirm if self.uuid is correct.
    #             self.add_connection(self, connection_id=self.uuid, session_id=self.session_id)
    #             return True
    #         else:
    #             self.sys_log.error("Payload type incorrect, Login Failed")
    #             return False
    #     else:
    #         self.sys_log.error("Incorrect credentials provided. Login Failed.")
    #         return False
    # %%

    def connect(self, **kwargs):
        """Send connect request."""
        self._connect(self, **kwargs)

    def _connect(self):
        """Do something."""
        pass
