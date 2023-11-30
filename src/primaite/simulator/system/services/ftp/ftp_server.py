from ipaddress import IPv4Address
from typing import Any, Dict, Optional

from primaite import getLogger
from primaite.simulator.network.protocols.ftp import FTPCommand, FTPPacket, FTPStatusCode
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.services.ftp.ftp_service import FTPServiceABC

_LOGGER = getLogger(__name__)


class FTPServer(FTPServiceABC):
    """
    A class for simulating an FTP server service.

    This class inherits from the `Service` class and provides methods to emulate FTP
    RFC 959: https://datatracker.ietf.org/doc/html/rfc959
    """

    server_password: Optional[str] = None
    """Password needed to connect to FTP server. Default is None."""

    connections: Dict[str, IPv4Address] = {}
    """Current active connections to the FTP server."""

    def __init__(self, **kwargs):
        kwargs["name"] = "FTPServer"
        kwargs["port"] = Port.FTP
        kwargs["protocol"] = IPProtocol.TCP
        super().__init__(**kwargs)
        self.start()

    def set_original_state(self):
        """Sets the original state."""
        _LOGGER.debug(f"Setting FTPServer original state on node {self.software_manager.node.hostname}")
        super().set_original_state()
        vals_to_include = {"server_password"}
        self._original_state.update(self.model_dump(include=vals_to_include))

    def reset_component_for_episode(self, episode: int):
        """Reset the original state of the SimComponent."""
        _LOGGER.debug(f"Resetting FTPServer state on node {self.software_manager.node.hostname}")
        self.connections.clear()
        super().reset_component_for_episode(episode)

    def _process_ftp_command(self, payload: FTPPacket, session_id: Optional[str] = None, **kwargs) -> FTPPacket:
        """
        Process the command in the FTP Packet.

        :param: payload: The FTP Packet to process
        :type: payload: FTPPacket
        :param: session_id: session ID linked to the FTP Packet. Optional.
        :type: session_id: Optional[str]
        """
        # error code by default
        payload.status_code = FTPStatusCode.ERROR

        # if server service is down, return error
        if not self._can_perform_action():
            return payload

        self.sys_log.info(f"{self.name}: Received FTP {payload.ftp_command.name} {payload.ftp_command_args}")

        if session_id:
            session_details = self._get_session_details(session_id)

        if payload.ftp_command is not None:
            self.sys_log.info(f"Received FTP {payload.ftp_command.name} command.")

        # process server specific commands, otherwise call super
        if payload.ftp_command == FTPCommand.PORT:
            # check that the port is valid
            if isinstance(payload.ftp_command_args, Port) and payload.ftp_command_args.value in range(0, 65535):
                # return successful connection
                self.connections[session_id] = session_details.with_ip_address
                payload.status_code = FTPStatusCode.OK
                return payload

            self.sys_log.error(f"Invalid Port {payload.ftp_command_args}")
            return payload

        if payload.ftp_command == FTPCommand.QUIT:
            self.connections.pop(session_id)
            payload.status_code = FTPStatusCode.OK
            return payload

        return super()._process_ftp_command(payload=payload, session_id=session_id, **kwargs)

    def receive(self, payload: Any, session_id: Optional[str] = None, **kwargs) -> bool:
        """Receives a payload from the SessionManager."""
        if not isinstance(payload, FTPPacket):
            self.sys_log.error(f"{payload} is not an FTP packet")
            return False

        if not super().receive(payload=payload, session_id=session_id, **kwargs):
            return False

        """
        Ignore ftp payload if status code is defined.

        This means that an FTP server has already handled the packet and
        prevents an FTP request loop - FTP client and servers can exist on
        the same node.
        """
        if payload.status_code is not None:
            return False

        self.send(self._process_ftp_command(payload=payload, session_id=session_id), session_id)
        return True
