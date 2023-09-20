from ipaddress import IPv4Address
from typing import Optional

from primaite.simulator.file_system.file_system import File
from primaite.simulator.network.protocols.ftp import FTPCommand, FTPPacket, FTPStatusCode
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.core.software_manager import SoftwareManager
from primaite.simulator.system.services.service import Service


class FTPClient(Service):
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
        self,
        ftp_server_ip_address: Optional[IPv4Address] = None,
    ) -> bool:
        # send a disconnect request payload to FTP server
        # return true if connected successfully else false
        self.connected = False

    def _process_response(self, payload: FTPPacket):
        """
        Process any FTPPacket responses.

        :param: payload: The FTPPacket payload
        :type: FTPPacket
        """
        if payload.ftp_command == FTPCommand.PORT:
            if payload.status_code == FTPStatusCode.OK:
                self.connected = True

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
            payload: FTPPacket = FTPPacket(
                ftp_command=FTPCommand.STOR,
                ftp_command_args={
                    "dest_folder_name": dest_folder_name,
                    "dest_file_name": dest_file_name,
                    "file_size": file_to_transfer.sim_size,
                },
                packet_payload_size=file_to_transfer.sim_size,
            )
            software_manager: SoftwareManager = self.software_manager
            software_manager.send_payload_to_session_manager(
                payload=payload, dest_ip_address=dest_ip_address, dest_port=dest_port
            )

            if payload.status_code == Port.FTP:
                self._disconnect_from_server()
                return True

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
        pass

    def receive(self, payload: FTPPacket, session_id: Optional[str] = None, **kwargs) -> bool:
        """Receives a payload from the SessionManager."""
        if not isinstance(payload, FTPPacket):
            self.sys_log.error(f"{payload} is not an FTP packet")
            return False

        self._process_response(payload=payload)
        return True
