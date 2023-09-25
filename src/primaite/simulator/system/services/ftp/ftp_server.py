from ipaddress import IPv4Address
from typing import Any, Dict, Optional

from primaite.simulator.network.protocols.ftp import FTPCommand, FTPPacket, FTPStatusCode
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.core.session_manager import Session
from primaite.simulator.system.services.ftp.ftp_service import FTPServiceABC
from primaite.simulator.system.services.service import ServiceOperatingState


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

    def _get_session_details(self, session_id: str) -> Session:
        """
        Returns the Session object from the given session id.

        :param: session_id: ID of the session that needs details retrieved
        """
        return self.software_manager.session_manager.sessions_by_uuid[session_id]

    def _process_ftp_command(self, payload: FTPPacket, session_id: Optional[str] = None, **kwargs) -> FTPPacket:
        """
        Process the command in the FTP Packet.

        :param: payload: The FTP Packet to process
        :type: payload: FTPPacket
        :param: session_id: session ID linked to the FTP Packet. Optional.
        :type: session_id: Optional[str]
        """
        # if server service is down, return error
        if self.operating_state != ServiceOperatingState.RUNNING:
            payload.status_code = FTPStatusCode.ERROR
            return payload

        if session_id:
            session_details = self._get_session_details(session_id)

        # process server specific commands, otherwise call super
        if payload.ftp_command == FTPCommand.PORT:
            # check that the port is valid
            if isinstance(payload.ftp_command_args, Port) and payload.ftp_command_args.value in range(0, 65535):
                # return successful connection
                self.connections[session_id] = session_details.with_ip_address
                payload.status_code = FTPStatusCode.OK
                return payload

        if payload.ftp_command == FTPCommand.QUIT:
            self.connections.pop(session_id)
            payload.status_code = FTPStatusCode.OK

        return super()._process_ftp_command(payload=payload, session_id=session_id, **kwargs)

    def receive(self, payload: Any, session_id: Optional[str] = None, **kwargs) -> bool:
        """Receives a payload from the SessionManager."""
        if not isinstance(payload, FTPPacket):
            self.sys_log.error(f"{payload} is not an FTP packet")
            return False

        self.send(self._process_ftp_command(payload=payload, session_id=session_id), session_id)
        return True
