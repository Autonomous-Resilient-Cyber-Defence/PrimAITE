# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from typing import Tuple

import pytest

from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.system.services.ftp.ftp_client import FTPClient
from primaite.simulator.system.services.ftp.ftp_server import FTPServer
from primaite.simulator.system.services.service import ServiceOperatingState


@pytest.fixture(scope="function")
def ftp_client_and_ftp_server(client_server) -> Tuple[FTPClient, Computer, FTPServer, Server]:
    computer, server = client_server

    # Install FTP Client service on computer
    computer.software_manager.install(FTPClient)
    ftp_client: FTPClient = computer.software_manager.software.get("FTPClient")
    ftp_client.start()

    # Install FTP Server service on server
    server.software_manager.install(FTPServer)
    ftp_server: FTPServer = server.software_manager.software.get("FTPServer")
    ftp_server.start()

    return ftp_client, computer, ftp_server, server


def test_ftp_client_store_file_in_server(ftp_client_and_ftp_server):
    """
    Test checks to see if the client is able to store files in the backup server.
    """
    ftp_client, computer, ftp_server, server = ftp_client_and_ftp_server

    assert ftp_client.operating_state == ServiceOperatingState.RUNNING
    assert ftp_server.operating_state == ServiceOperatingState.RUNNING

    # create file on ftp client
    ftp_client.file_system.create_file(file_name="test_file.txt")

    assert ftp_client.send_file(
        src_folder_name="root",
        src_file_name="test_file.txt",
        dest_folder_name="client_1_backup",
        dest_file_name="test_file.txt",
        dest_ip_address=server.network_interfaces.get(next(iter(server.network_interfaces))).ip_address,
    )

    assert ftp_server.file_system.get_file(folder_name="client_1_backup", file_name="test_file.txt")


def test_ftp_client_retrieve_file_from_server(ftp_client_and_ftp_server):
    """
    Test checks to see if the client is able to retrieve files from the backup server.
    """
    ftp_client, computer, ftp_server, server = ftp_client_and_ftp_server

    assert ftp_client.operating_state == ServiceOperatingState.RUNNING
    assert ftp_server.operating_state == ServiceOperatingState.RUNNING

    # create file on ftp server
    ftp_server.file_system.create_file(file_name="test_file.txt", folder_name="file_share")

    assert ftp_client.request_file(
        src_folder_name="file_share",
        src_file_name="test_file.txt",
        dest_folder_name="downloads",
        dest_file_name="test_file.txt",
        dest_ip_address=server.network_interfaces.get(next(iter(server.network_interfaces))).ip_address,
    )

    # client should have retrieved the file
    assert ftp_client.file_system.get_file(folder_name="downloads", file_name="test_file.txt")


def test_ftp_client_tries_to_connect_to_offline_server(ftp_client_and_ftp_server):
    """Test checks to make sure that the client can't do anything when the server is offline."""
    ftp_client, computer, ftp_server, server = ftp_client_and_ftp_server

    assert ftp_client.operating_state == ServiceOperatingState.RUNNING
    assert ftp_server.operating_state == ServiceOperatingState.RUNNING

    # create file on ftp server
    ftp_server.file_system.create_file(file_name="test_file.txt", folder_name="file_share")

    server.power_off()

    for i in range(server.shut_down_duration + 1):
        server.apply_timestep(timestep=i)

    assert ftp_client.operating_state == ServiceOperatingState.RUNNING
    assert ftp_server.operating_state == ServiceOperatingState.STOPPED

    assert (
        ftp_client.request_file(
            src_folder_name="file_share",
            src_file_name="test_file.txt",
            dest_folder_name="downloads",
            dest_file_name="test_file.txt",
            dest_ip_address=server.network_interfaces.get(next(iter(server.network_interfaces))).ip_address,
        )
        is False
    )

    # client should have retrieved the file
    assert ftp_client.file_system.get_file(folder_name="downloads", file_name="test_file.txt") is None
