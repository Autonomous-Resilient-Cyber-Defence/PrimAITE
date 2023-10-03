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
    """Keeps track of whether or not the FTP client is connected to an FTP server."""

    def __init__(self, **kwargs):
        kwargs["name"] = "FTPClient"
        kwargs["port"] = Port.FTP
        kwargs["protocol"] = IPProtocol.TCP
        super().__init__(**kwargs)
        self.start()

    def _process_ftp_command(self, payload: FTPPacket, session_id: Optional[str] = None, **kwargs) -> FTPPacket:
        """
        Process the command in the FTP Packet.

        :param: payload: The FTP Packet to process
        :type: payload: FTPPacket
        :param: session_id: session ID linked to the FTP Packet. Optional.
        :type: session_id: Optional[str]
        """
        # if client service is down, return error
        if self.operating_state != ServiceOperatingState.RUNNING:
            self.sys_log.error("FTP Client is not running")
            payload.status_code = FTPStatusCode.ERROR
            return payload

        self.sys_log.info(f"{self.name}: Received FTP {payload.ftp_command.name} {payload.ftp_command_args}")

        # process client specific commands, otherwise call super
        return super()._process_ftp_command(payload=payload, session_id=session_id, **kwargs)

    def _connect_to_server(
        self,
        dest_ip_address: Optional[IPv4Address] = None,
        dest_port: Optional[Port] = Port.FTP,
        session_id: Optional[str] = None,
        is_reattempt: Optional[bool] = False,
    ) -> bool:
        """
        Connects the client to a given FTP server.

        :param: dest_ip_address: IP address of the FTP server the client needs to connect to. Optional.
        :type: dest_ip_address: Optional[IPv4Address]
        :param: dest_port: Port of the FTP server the client needs to connect to. Optional.
        :type: dest_port: Optional[Port]
        :param: is_reattempt: Set to True if attempt to connect to FTP Server has been attempted. Default False.
        :type: is_reattempt: Optional[bool]
        """
        # make sure the service is running before attempting
        if self.operating_state != ServiceOperatingState.RUNNING:
            self.sys_log.error(f"FTPClient not running for {self.sys_log.hostname}")
            return False

        # normally FTP will choose a random port for the transfer, but using the FTP command port will do for now
        # create FTP packet
        payload: FTPPacket = FTPPacket(
            ftp_command=FTPCommand.PORT,
            ftp_command_args=Port.FTP,
        )

        if self.send(payload=payload, dest_ip_address=dest_ip_address, dest_port=dest_port, session_id=session_id):
            if payload.status_code == FTPStatusCode.OK:
                self.sys_log.info(
                    f"{self.name}: Successfully connected to FTP Server "
                    f"{dest_ip_address} via port {payload.ftp_command_args.value}"
                )
                return True
            else:
                if is_reattempt:
                    # reattempt failed
                    self.sys_log.info(
                        f"{self.name}: Unable to connect to FTP Server "
                        f"{dest_ip_address} via port {payload.ftp_command_args.value}"
                    )
                    return False
                else:
                    # try again
                    self._connect_to_server(
                        dest_ip_address=dest_ip_address, dest_port=dest_port, session_id=session_id, is_reattempt=True
                    )

    def _disconnect_from_server(
        self, dest_ip_address: Optional[IPv4Address] = None, dest_port: Optional[Port] = Port.FTP
    ) -> bool:
        """
        Connects the client from a given FTP server.

        :param: dest_ip_address: IP address of the FTP server the client needs to disconnect from. Optional.
        :type: dest_ip_address: Optional[IPv4Address]
        :param: dest_port: Port of the FTP server the client needs to disconnect from. Optional.
        :type: dest_port: Optional[Port]
        :param: is_reattempt: Set to True if attempt to disconnect from FTP Server has been attempted. Default False.
        :type: is_reattempt: Optional[bool]
        """
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
        session_id: Optional[str] = None,
    ) -> bool:
        """
        Send a file to a target IP address.

        The function checks if the file exists in the FTP Client host.
        The STOR command is then sent to the FTP Server.

        :param: dest_ip_address: The IP address of the machine that hosts the FTP Server.
        :type: dest_ip_address: IPv4Address

        :param: src_folder_name: The name of the folder that contains the file to send to the FTP Server.
        :type: src_folder_name: str

        :param: src_file_name: The name of the file to send to the FTP Server.
        :type: src_file_name: str

        :param: dest_folder_name: The name of the folder where the file will be stored in the FTP Server.
        :type: dest_folder_name: str

        :param: dest_file_name: The name of the file to be saved on the FTP Server.
        :type: dest_file_name: str

        :param: dest_port: The open port of the machine that hosts the FTP Server. Default is Port.FTP.
        :type: dest_port: Optional[Port]

        :param: session_id: The id of the session
        :type: session_id: Optional[str]
        """
        # check if the file to transfer exists on the client
        file_to_transfer: File = self.file_system.get_file(folder_name=src_folder_name, file_name=src_file_name)
        if not file_to_transfer:
            self.sys_log.error(f"Unable to send file that does not exist: {src_folder_name}/{src_file_name}")
            return False

        # check if FTP is currently connected to IP
        self.connected = self._connect_to_server(dest_ip_address=dest_ip_address, dest_port=dest_port)

        if not self.connected:
            return False
        else:
            # send STOR request
            self._send_data(
                file=file_to_transfer,
                dest_folder_name=dest_folder_name,
                dest_file_name=dest_file_name,
                dest_ip_address=dest_ip_address,
                dest_port=dest_port,
                session_id=session_id,
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
    ) -> bool:
        """
        Request a file from a target IP address.

        Sends a RETR command to the FTP Server.

        :param: dest_ip_address: The IP address of the machine that hosts the FTP Server.
        :type: dest_ip_address: IPv4Address

        :param: src_folder_name: The name of the folder that contains the file to send to the FTP Server.
        :type: src_folder_name: str

        :param: src_file_name: The name of the file to send to the FTP Server.
        :type: src_file_name: str

        :param: dest_folder_name: The name of the folder where the file will be stored in the FTP Server.
        :type: dest_folder_name: str

        :param: dest_file_name: The name of the file to be saved on the FTP Server.
        :type: dest_file_name: str

        :param: dest_port: The open port of the machine that hosts the FTP Server. Default is Port.FTP.
        :type: dest_port: Optional[Port]
        """
        # check if FTP is currently connected to IP
        self.connected = self._connect_to_server(dest_ip_address=dest_ip_address, dest_port=dest_port)

        if not self.connected:
            return False
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
                self.sys_log.info(f"{self.name}: File {src_folder_name}/{src_file_name} found in FTP server.")
                return True
            else:
                self.sys_log.error(f"{self.name}: File {src_folder_name}/{src_file_name} does not exist in FTP server")
                return False

    def send(
        self,
        payload: FTPPacket,
        session_id: Optional[str] = None,
        dest_ip_address: Optional[IPv4Address] = None,
        dest_port: Optional[Port] = None,
        **kwargs,
    ) -> bool:
        """
        Sends a payload to the SessionManager.

        :param payload: The payload to be sent.
        :param dest_ip_address: The ip address of the payload destination.
        :param dest_port: The port of the payload destination.
        :param session_id: The Session ID the payload is to originate from. Optional.

        :return: True if successful, False otherwise.
        """
        self.sys_log.info(f"{self.name}: Sending FTP {payload.ftp_command.name} {payload.ftp_command_args}")

        return super().send(
            payload=payload, dest_ip_address=dest_ip_address, dest_port=dest_port, session_id=session_id, **kwargs
        )

    def receive(self, payload: FTPPacket, session_id: Optional[str] = None, **kwargs) -> bool:
        """
        Receives a payload from the SessionManager.

        :param: payload: FTPPacket payload.
        :type: payload: FTPPacket

        :param: session_id: ID of the session. Optional.
        :type: session_id: Optional[str]
        """
        if not isinstance(payload, FTPPacket):
            self.sys_log.error(f"{payload} is not an FTP packet")
            return False

        self._process_ftp_command(payload=payload, session_id=session_id)
        return True
