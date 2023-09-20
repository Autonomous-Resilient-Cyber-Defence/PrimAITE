from typing import Any, Optional

from primaite.simulator.network.protocols.ftp import FTPCommand, FTPPacket, FTPStatusCode
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.services.service import Service


class FTPServer(Service):
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

    def _process_ftp_command(self, payload: FTPPacket) -> FTPPacket:
        # handle PORT request
        if payload.ftp_command == FTPCommand.PORT:
            # check that the port is valid
            if isinstance(payload.ftp_command_args, Port) and payload.ftp_command_args.value in range(0, 65535):
                # return successful connection
                payload.status_code = FTPStatusCode.OK

        # handle STOR request
        if payload.ftp_command == FTPCommand.STOR:
            # check that the file is created in the computed hosting the FTP server
            if self._process_store_data(payload=payload):
                payload.status_code = FTPStatusCode.OK

        return payload

    def _process_store_data(self, payload: FTPPacket) -> bool:
        """Handle the transfer of data from Client to this Server."""
        try:
            file_name = payload.ftp_command_args["dest_file_name"]
            folder_name = payload.ftp_command_args["dest_folder_name"]
            file_size = payload.ftp_command_args["file_size"]
            self.file_system.create_file(
                file_name=file_name,
                folder_name=folder_name,
                size=file_size,
            )
            self.sys_log.info(
                f"Created item in {self.name}: {payload.ftp_command_args['dest_folder_name']}/"
                f"{payload.ftp_command_args['dest_file_name']}"
            )
            # file should exist
            return self.file_system.get_file(file_name=file_name, folder_name=folder_name) is not None
        except Exception as e:
            self.sys_log.error(f"Unable to store file in {self.name}: {e}")
            return False

    def receive(self, payload: Any, session_id: Optional[str] = None, **kwargs) -> bool:
        """Receives a payload from the SessionManager."""
        if not isinstance(payload, FTPPacket):
            self.sys_log.error(f"{payload} is not an FTP packet")
            return False

        self.send(self._process_ftp_command(payload=payload), session_id)
        return True
