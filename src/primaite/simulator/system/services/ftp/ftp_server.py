# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
"""FTP Server."""
from typing import Any, Optional

from pydantic import Field

from primaite import getLogger
from primaite.simulator.network.protocols.ftp import FTPCommand, FTPPacket, FTPStatusCode
from primaite.simulator.system.services.ftp.ftp_service import FTPServiceABC
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.port import is_valid_port, PORT_LOOKUP

_LOGGER = getLogger(__name__)


class FTPServer(FTPServiceABC, discriminator="ftp-server"):
    """
    A class for simulating an FTP server service.

    This class inherits from the `FTPServiceABC` class and provides methods to emulate FTP
    RFC 959: https://datatracker.ietf.org/doc/html/rfc959
    """

    class ConfigSchema(FTPServiceABC.ConfigSchema):
        """ConfigSchema for FTPServer."""

        type: str = "ftp-server"
        server_password: Optional[str] = None

    config: ConfigSchema = Field(default_factory=lambda: FTPServer.ConfigSchema())
    server_password: Optional[str] = None

    def __init__(self, **kwargs):
        kwargs["name"] = "ftp-server"
        kwargs["port"] = PORT_LOOKUP["FTP"]
        kwargs["protocol"] = PROTOCOL_LOOKUP["TCP"]
        super().__init__(**kwargs)
        self.start()

    @property
    def server_password(self) -> Optional[str]:
        """Convenience method for accessing FTP server password."""
        return self.config.server_password

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

        if payload.ftp_command is not None:
            self.sys_log.info(f"Received FTP {payload.ftp_command.name} command.")

        # process server specific commands, otherwise call super
        if payload.ftp_command == FTPCommand.PORT:
            # check that the port is valid
            if is_valid_port(payload.ftp_command_args):
                # return successful connection
                self.add_connection(connection_id=session_id, session_id=session_id)
                payload.status_code = FTPStatusCode.OK
                return payload

            self.sys_log.error(f"Invalid Port {payload.ftp_command_args}")
            return payload

        if payload.ftp_command == FTPCommand.QUIT:
            self.terminate_connection(connection_id=session_id)
            payload.status_code = FTPStatusCode.OK
            return payload

        return super()._process_ftp_command(payload=payload, session_id=session_id, **kwargs)

    def receive(self, payload: Any, session_id: Optional[str] = None, **kwargs) -> bool:
        """Receives a payload from the SessionManager."""
        if not isinstance(payload, FTPPacket):
            self.sys_log.warning(f"{self.name}: Payload is not an FTP packet")
            self.sys_log.debug(f"{self.name}: {payload}")
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

        self._process_ftp_command(payload=payload, session_id=session_id)
        return True
