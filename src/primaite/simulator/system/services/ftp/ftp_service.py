from abc import ABC
from ipaddress import IPv4Address
from typing import Optional

from primaite.simulator.file_system.file_system import File
from primaite.simulator.network.protocols.ftp import FTPCommand, FTPPacket, FTPStatusCode
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.core.software_manager import SoftwareManager
from primaite.simulator.system.services.service import Service


class FTPServiceABC(Service, ABC):
    """
    Abstract Base Class for FTP Client and Service.

    Contains shared methods between both classes.
    """

    def _process_ftp_command(self, payload: FTPPacket, session_id: Optional[str] = None, **kwargs) -> FTPPacket:
        # handle STOR request
        if payload.ftp_command == FTPCommand.STOR:
            # check that the file is created in the computed hosting the FTP server
            if self._store_data(payload=payload):
                payload.status_code = FTPStatusCode.OK

        if payload.ftp_command == FTPCommand.RETR:
            # check that the file exists in the FTP Server
            file: File = self.file_system.get_file(
                folder_name=payload.ftp_command_args["src_folder_name"],
                file_name=payload.ftp_command_args["src_file_name"],
            )
            if file:
                payload.status_code = FTPStatusCode.OK
                self._send_data(
                    file=file,
                    dest_folder_name=payload.ftp_command_args["dest_folder_name"],
                    dest_file_name=payload.ftp_command_args["dest_file_name"],
                    session_id=session_id,
                )

        return payload

    def _store_data(self, payload: FTPPacket) -> bool:
        """
        Handle the transfer of data.

        :param: payload: The FTP Packet that contains the file data
        :type: FTPPacket
        """
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
                f"Created item in {self.sys_log.hostname}: {payload.ftp_command_args['dest_folder_name']}/"
                f"{payload.ftp_command_args['dest_file_name']}"
            )
            # file should exist
            return self.file_system.get_file(file_name=file_name, folder_name=folder_name) is not None
        except Exception as e:
            self.sys_log.error(f"Unable to create file in {self.sys_log.hostname}: {e}")
            return False

    def _send_data(
        self,
        file: File,
        dest_folder_name: str,
        dest_file_name: str,
        dest_ip_address: Optional[IPv4Address] = None,
        dest_port: Optional[Port] = None,
        session_id: Optional[str] = None,
    ) -> bool:
        # send STOR request
        payload: FTPPacket = FTPPacket(
            ftp_command=FTPCommand.STOR,
            ftp_command_args={
                "dest_folder_name": dest_folder_name,
                "dest_file_name": dest_file_name,
                "file_size": file.sim_size,
            },
            packet_payload_size=file.sim_size,
        )
        software_manager: SoftwareManager = self.software_manager
        software_manager.send_payload_to_session_manager(
            payload=payload, dest_ip_address=dest_ip_address, dest_port=dest_port, session_id=session_id
        )

        if payload.status_code == FTPStatusCode.OK:
            return True

        return False

    def _retrieve_data(self, payload: FTPPacket, session_id: Optional[str] = None) -> bool:
        """
        Handle the transfer of data from Server to Client.

        :param: payload: The FTP Packet that contains the file data
        :type: FTPPacket
        """
        try:
            # find the file
            file_name = payload.ftp_command_args["src_file_name"]
            folder_name = payload.ftp_command_args["src_folder_name"]
            retrieved_file: File = self.file_system.get_file(folder_name=folder_name, file_name=file_name)

            # if file does not exist, return an error
            if not retrieved_file:
                self.sys_log.error(
                    f"File  {payload.ftp_command_args['dest_folder_name']}/"
                    f"{payload.ftp_command_args['dest_file_name']} does not exist in {self.sys_log.hostname}"
                )
                return False
            else:
                # send requested data
                return self._send_data(
                    file=retrieved_file, dest_file_name=file_name, dest_folder_name=folder_name, session_id=session_id
                )
        except Exception as e:
            self.sys_log.error(f"Unable to retrieve file from {self.sys_log.hostname}: {e}")
            return False
