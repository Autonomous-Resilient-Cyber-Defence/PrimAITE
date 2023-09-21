from typing import Any, Optional

from primaite.simulator.network.protocols.ftp import FTPPacket
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.services.ftp.ftp_service import FTPServiceABC


class FTPServer(FTPServiceABC):
    """
    A class for simulating an FTP server service.

    This class inherits from the `Service` class and provides methods to emulate FTP
    RFC 959: https://datatracker.ietf.org/doc/html/rfc959
    """

    server_password: Optional[str] = None
    """Password needed to connect to FTP server. Default is None."""

    def __init__(self, **kwargs):
        kwargs["name"] = "FTPServer"
        kwargs["port"] = Port.FTP
        kwargs["protocol"] = IPProtocol.TCP
        super().__init__(**kwargs)
        self.start()

    def receive(self, payload: Any, session_id: Optional[str] = None, **kwargs) -> bool:
        """Receives a payload from the SessionManager."""
        if not isinstance(payload, FTPPacket):
            self.sys_log.error(f"{payload} is not an FTP packet")
            return False

        self.send(self._process_ftp_command(payload=payload, session_id=session_id), session_id)
        return True
