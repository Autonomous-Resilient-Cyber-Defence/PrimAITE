# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from ipaddress import IPv4Address
from typing import Dict, Optional

from pydantic import Field

from primaite import getLogger
from primaite.interface.request import RequestFormat, RequestResponse
from primaite.simulator.core import RequestManager, RequestType
from primaite.simulator.file_system.file_system import File
from primaite.simulator.network.protocols.ftp import FTPCommand, FTPPacket, FTPStatusCode
from primaite.simulator.system.core.software_manager import SoftwareManager
from primaite.simulator.system.services.ftp.ftp_service import FTPServiceABC
from primaite.simulator.system.services.service import Service
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.port import Port, PORT_LOOKUP

_LOGGER = getLogger(__name__)


class FTPClient(FTPServiceABC, identifier="FTPClient"):
    """
    A class for simulating an FTP client service.

    This class inherits from the `FTPServiceABC` class and provides methods to emulate FTP
    RFC 959: https://datatracker.ietf.org/doc/html/rfc959
    """

    config: "FTPClient.ConfigSchema" = Field(default_factory=lambda: FTPClient.ConfigSchema())

    class ConfigSchema(Service.ConfigSchema):
        """ConfigSchema for FTPClient."""

        type: str = "FTPClient"

    def __init__(self, **kwargs):
        kwargs["name"] = "FTPClient"
        kwargs["port"] = PORT_LOOKUP["FTP"]
        kwargs["protocol"] = PROTOCOL_LOOKUP["TCP"]
        super().__init__(**kwargs)
        self.start()

    def _init_request_manager(self) -> RequestManager:
        """
        Initialise the request manager.

        More information in user guide and docstring for SimComponent._init_request_manager.
        """
        rm = super()._init_request_manager()

        def _send_data_request(request: RequestFormat, context: Dict) -> RequestResponse:
            """
            Request for sending data via the ftp_client using the request options parameters.

            :param request: Request with one element containing a dict of parameters for the send method.
            :type request: RequestFormat
            :param context: additional context for resolving this action, currently unused
            :type context: dict
            :return: RequestResponse object with a success code reflecting whether the configuration could be applied.
            :rtype: RequestResponse
            """
            dest_ip = request[-1].get("dest_ip_address")
            dest_ip = None if dest_ip is None else IPv4Address(dest_ip)

            # Missing FTP Options results is an automatic failure.
            src_folder = request[-1].get("src_folder_name", None)
            src_file_name = request[-1].get("src_file_name", None)
            dest_folder = request[-1].get("dest_folder_name", None)
            dest_file_name = request[-1].get("dest_file_name", None)

            if not self.file_system.access_file(folder_name=src_folder, file_name=src_file_name):
                self.sys_log.debug(
                    f"{self.name}: Received a FTP Request to transfer file: {src_file_name} to Remote IP: {dest_ip}."
                )
                return RequestResponse(
                    status="failure",
                    data={
                        "reason": "Unable to locate given file on local file system. Perhaps given options are invalid?"
                    },
                )

            return RequestResponse.from_bool(
                self.send_file(
                    dest_ip_address=dest_ip,
                    src_folder_name=src_folder,
                    src_file_name=src_file_name,
                    dest_folder_name=dest_folder,
                    dest_file_name=dest_file_name,
                )
            )

        rm.add_request("send", request_type=RequestType(func=_send_data_request)),
        return rm

    def _process_ftp_command(self, payload: FTPPacket, session_id: Optional[str] = None, **kwargs) -> FTPPacket:
        """
        Process the command in the FTP Packet.

        :param: payload: The FTP Packet to process
        :type: payload: FTPPacket
        :param: session_id: session ID linked to the FTP Packet. Optional.
        :type: session_id: Optional[str]
        """
        # if client service is down, return error
        if not self._can_perform_action():
            payload.status_code = FTPStatusCode.ERROR
            return payload

        self.sys_log.info(f"{self.name}: Received FTP {payload.ftp_command.name} {payload.ftp_command_args}")

        # process client specific commands, otherwise call super
        return super()._process_ftp_command(payload=payload, session_id=session_id, **kwargs)

    def _connect_to_server(
        self,
        dest_ip_address: Optional[IPv4Address] = None,
        dest_port: Optional[Port] = PORT_LOOKUP["FTP"],
        session_id: Optional[str] = None,
        is_reattempt: Optional[bool] = False,
    ) -> bool:
        self._active = True
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
        if not self._can_perform_action():
            return False

        # normally FTP will choose a random port for the transfer, but using the FTP command port will do for now
        # create FTP packet
        payload: FTPPacket = FTPPacket(ftp_command=FTPCommand.PORT, ftp_command_args=PORT_LOOKUP["FTP"])

        if self.send(payload=payload, dest_ip_address=dest_ip_address, dest_port=dest_port, session_id=session_id):
            if payload.status_code == FTPStatusCode.OK:
                self.sys_log.info(
                    f"{self.name}: Successfully connected to FTP Server "
                    f"{dest_ip_address} via port {payload.ftp_command_args}"
                )
                self.add_connection(connection_id="server_connection", session_id=session_id)
                return True
            else:
                if is_reattempt:
                    # reattempt failed
                    self.sys_log.warning(
                        f"{self.name}: Unable to connect to FTP Server "
                        f"{dest_ip_address} via port {payload.ftp_command_args}"
                    )
                    return False
                else:
                    # try again
                    self._connect_to_server(
                        dest_ip_address=dest_ip_address, dest_port=dest_port, session_id=session_id, is_reattempt=True
                    )
        else:
            self.sys_log.warning(f"{self.name}: Unable to send FTPPacket")
            return False

    def _disconnect_from_server(
        self, dest_ip_address: Optional[IPv4Address] = None, dest_port: Optional[Port] = PORT_LOOKUP["FTP"]
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
        self._active = True
        # send a disconnect request payload to FTP server
        payload: FTPPacket = FTPPacket(ftp_command=FTPCommand.QUIT)
        software_manager: SoftwareManager = self.software_manager
        software_manager.send_payload_to_session_manager(
            payload=payload, dest_ip_address=dest_ip_address, dest_port=dest_port
        )
        return payload.status_code == FTPStatusCode.OK

    def send_file(
        self,
        dest_ip_address: IPv4Address,
        src_folder_name: str,
        src_file_name: str,
        dest_folder_name: str,
        dest_file_name: str,
        dest_port: Optional[Port] = PORT_LOOKUP["FTP"],
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

        :param: dest_port: The open port of the machine that hosts the FTP Server. Default is Port["FTP"].
        :type: dest_port: Optional[Port]

        :param: session_id: The id of the session
        :type: session_id: Optional[str]
        """
        self._active = True
        # check if the file to transfer exists on the client
        file_to_transfer: File = self.file_system.get_file(folder_name=src_folder_name, file_name=src_file_name)
        if not file_to_transfer:
            self.sys_log.warning(f"Unable to send file that does not exist: {src_folder_name}/{src_file_name}")
            return False

        # check if FTP is currently connected to IP
        self._connect_to_server(dest_ip_address=dest_ip_address, dest_port=dest_port)

        if not len(self.connections):
            return False
        else:
            self.sys_log.info(f"Sending file {src_folder_name}/{src_file_name} to {str(dest_ip_address)}")
            # send STOR request
            if self._send_data(
                file=file_to_transfer,
                dest_folder_name=dest_folder_name,
                dest_file_name=dest_file_name,
                dest_ip_address=dest_ip_address,
                dest_port=dest_port,
            ):
                return self._disconnect_from_server(dest_ip_address=dest_ip_address, dest_port=dest_port)

            return False

    def request_file(
        self,
        dest_ip_address: IPv4Address,
        src_folder_name: str,
        src_file_name: str,
        dest_folder_name: str,
        dest_file_name: str,
        dest_port: Optional[Port] = PORT_LOOKUP["FTP"],
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

        :param: dest_port: The open port of the machine that hosts the FTP Server. Default is Port["FTP"].
        :type: dest_port: Optional[int]
        """
        self._active = True
        # check if FTP is currently connected to IP
        self._connect_to_server(dest_ip_address=dest_ip_address, dest_port=dest_port)

        if not len(self.connections):
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
            self.sys_log.info(f"Requesting file {src_folder_name}/{src_file_name} from {str(dest_ip_address)}")
            software_manager: SoftwareManager = self.software_manager
            software_manager.send_payload_to_session_manager(
                payload=payload, dest_ip_address=dest_ip_address, dest_port=dest_port
            )

            # the payload should have ok status code
            if payload.status_code == FTPStatusCode.OK:
                self.sys_log.info(f"{self.name}: File {src_folder_name}/{src_file_name} found in FTP server.")
                return True
            else:
                self.sys_log.error(f"{self.name}: File {src_folder_name}/{src_file_name} does not exist in FTP server")
                return False

    def receive(self, payload: FTPPacket, session_id: Optional[str] = None, **kwargs) -> bool:
        """
        Receives a payload from the SessionManager.

        :param: payload: FTPPacket payload.
        :type: payload: FTPPacket

        :param: session_id: ID of the session. Optional.
        :type: session_id: Optional[str]
        """
        if not isinstance(payload, FTPPacket):
            self.sys_log.warning(f"{self.name}: Payload is not an FTP packet")
            self.sys_log.debug(f"{self.name}: {payload}")
            return False

        """
        Ignore ftp payload if status code is None.

        This helps prevent an FTP request loop - FTP client and servers can exist on
        the same node.
        """
        self._active = True
        if not self._can_perform_action():
            return False

        if payload.status_code is None:
            self.sys_log.error(f"FTP Server could not be found - Error Code: {FTPStatusCode.NOT_FOUND.value}")
            return False

        # if PORT succeeded, add the connection as an active connection list
        if payload.ftp_command is FTPCommand.PORT and payload.status_code is FTPStatusCode.OK:
            self.add_connection(connection_id=session_id, session_id=session_id)

        # if QUIT succeeded, remove the session from active connection list
        if payload.ftp_command is FTPCommand.QUIT and payload.status_code is FTPStatusCode.OK:
            self.terminate_connection(connection_id=session_id)

        self.sys_log.info(f"{self.name}: Received FTP Response {payload.ftp_command.name} {payload.status_code.value}")

        self._process_ftp_command(payload=payload, session_id=session_id)
        return True
