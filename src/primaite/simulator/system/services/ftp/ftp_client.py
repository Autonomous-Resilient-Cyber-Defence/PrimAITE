from ipaddress import IPv4Address
from typing import Optional

from primaite.simulator.file_system.file_system import File
from primaite.simulator.network.protocols.ftp import FTPCommand, FTPPacket, FTPStatusCode
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.core.software_manager import SoftwareManager
from primaite.simulator.system.services.ftp.ftp_service import FTPServiceABC
from primaite.simulator.system.services.service import ServiceOperatingState


class FTPClient(FTPServiceABC):
    """
    A class for simulating an FTP client service.

    This class inherits from the `Service` class and provides methods to emulate FTP
    RFC 959: https://datatracker.ietf.org/doc/html/rfc959
    """

    connected: bool = False
    """Keeps track of whether or not the FTP client is connected to an FTP server"""

    def __init__(self, **kwargs):
        kwargs["name"] = "FTPClient"
        kwargs["port"] = Port.FTP
        kwargs["protocol"] = IPProtocol.TCP
        super().__init__(**kwargs)
        self.start()

    def _process_ftp_command(self, payload: FTPPacket, session_id: Optional[str] = None, **kwargs) -> FTPPacket:
        # if server is down, return error
        if self.operating_state != ServiceOperatingState.RUNNING:
            payload.status_code = FTPStatusCode.ERROR
            return payload

        # process client specific commands, otherwise call super
        return super()._process_ftp_command(payload=payload, session_id=session_id, **kwargs)

    def _connect_to_server(
        self, dest_ip_address: Optional[IPv4Address] = None, dest_port: Optional[Port] = Port.FTP
    ) -> bool:
        """
        Connects the client to a given FTP server.

        :param: dest_ip_address: IP address of the FTP server the client needs to connect to. Optional.
        :type: Optional[IPv4Address]
        :param: dest_port: Port of the FTP server the client needs to connect to. Optional.
        :type: Optional[Port]
        :param: server_password: The password to use when connecting to the FTP server. Optional.
        :type: Optional[str]
        """
        # normally FTP will choose a random port for the transfer, but using the FTP command port will do for now

        # create FTP packet
        payload: FTPPacket = FTPPacket(
            ftp_command=FTPCommand.PORT,
            ftp_command_args=Port.FTP,
        )
        software_manager: SoftwareManager = self.software_manager
        software_manager.send_payload_to_session_manager(
            payload=payload, dest_ip_address=dest_ip_address, dest_port=dest_port
        )
        return payload.status_code == FTPStatusCode.OK

    def _disconnect_from_server(
        self, dest_ip_address: Optional[IPv4Address] = None, dest_port: Optional[Port] = Port.FTP
    ) -> bool:
        # send a disconnect request payload to FTP server
        payload: FTPPacket = FTPPacket(ftp_command=FTPCommand.QUIT)
        software_manager: SoftwareManager = self.software_manager
        software_manager.send_payload_to_session_manager(
            payload=payload, dest_ip_address=dest_ip_address, dest_port=dest_port
        )
        if payload.status_code == FTPStatusCode.OK:
            self.connected = False
            return True
        return False

    def send_file(
        self,
        dest_ip_address: IPv4Address,
        src_folder_name: str,
        src_file_name: str,
        dest_folder_name: str,
        dest_file_name: str,
        dest_port: Optional[Port] = Port.FTP,
        is_reattempt: Optional[bool] = False,
    ) -> bool:
        """Send a file to a target IP address."""
        # if service is not running, return error
        if self.operating_state != ServiceOperatingState.RUNNING:
            self.sys_log.error(f"FTPClient not running for {self.sys_log.hostname}")
            return False
        file_to_transfer: File = self.file_system.get_file(folder_name=src_folder_name, file_name=src_file_name)
        if not file_to_transfer:
            self.sys_log.error(f"Unable to send file that does not exist: {src_folder_name}/{src_file_name}")
            return False

        # check if FTP is currently connected to IP
        self.connected = self._connect_to_server(
            dest_ip_address=dest_ip_address,
            dest_port=dest_port,
        )

        if not self.connected:
            if is_reattempt:
                return False

            return self.send_file(
                src_folder_name=file_to_transfer.folder.name,
                src_file_name=file_to_transfer.name,
                dest_folder_name=dest_folder_name,
                dest_file_name=dest_file_name,
                dest_ip_address=dest_ip_address,
                dest_port=dest_port,
                is_reattempt=True,
            )
        else:
            # send STOR request
            self._send_data(
                file=file_to_transfer,
                dest_folder_name=dest_folder_name,
                dest_file_name=dest_file_name,
                dest_ip_address=dest_ip_address,
                dest_port=dest_port,
            )

            # send disconnect
            return self._disconnect_from_server(dest_ip_address=dest_ip_address, dest_port=dest_port)

    def request_file(
        self,
        dest_ip_address: IPv4Address,
        src_folder_name: str,
        src_file_name: str,
        dest_folder_name: str,
        dest_file_name: str,
        dest_port: Optional[Port] = Port.FTP,
        is_reattempt: Optional[bool] = False,
    ) -> bool:
        """Request a file from a target IP address."""
        # if service is not running, return error
        if self.operating_state != ServiceOperatingState.RUNNING:
            self.sys_log.error(f"FTPClient not running for {self.sys_log.hostname}")
            return False
        # check if FTP is currently connected to IP
        self.connected = self._connect_to_server(
            dest_ip_address=dest_ip_address,
            dest_port=dest_port,
        )

        if not self.connected:
            if is_reattempt:
                return False

            return self.request_file(
                src_folder_name=src_folder_name,
                src_file_name=src_file_name,
                dest_folder_name=dest_folder_name,
                dest_file_name=dest_file_name,
                dest_ip_address=dest_ip_address,
                dest_port=dest_port,
                is_reattempt=True,
            )
        else:
            # send retrieve request
            payload: FTPPacket = FTPPacket(
                ftp_command=FTPCommand.RETR,
                ftp_command_args={
                    "src_folder_name": src_folder_name,
                    "src_file_name": src_file_name,
                    "dest_file_name": dest_file_name,
                    "dest_folder_name": dest_folder_name,
                },
            )
            software_manager: SoftwareManager = self.software_manager
            software_manager.send_payload_to_session_manager(
                payload=payload, dest_ip_address=dest_ip_address, dest_port=dest_port
            )

            # send disconnect
            self._disconnect_from_server(dest_ip_address=dest_ip_address, dest_port=dest_port)

            # the payload should have ok status code
            if payload.status_code == FTPStatusCode.OK:
                self.sys_log.info(f"File {src_folder_name}/{src_file_name} found in FTP server.")
                return True
            else:
                self.sys_log.error(f"File {src_folder_name}/{src_file_name} does not exist in FTP server")
                return False

    def receive(self, payload: FTPPacket, session_id: Optional[str] = None, **kwargs) -> bool:
        """Receives a payload from the SessionManager."""
        if not isinstance(payload, FTPPacket):
            self.sys_log.error(f"{payload} is not an FTP packet")
            return False

        self._process_ftp_command(payload=payload, session_id=session_id)
        return True
