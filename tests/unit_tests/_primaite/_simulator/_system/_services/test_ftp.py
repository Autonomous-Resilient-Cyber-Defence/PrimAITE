from ipaddress import IPv4Address

import pytest

from primaite.simulator.network.hardware.base import Node
from primaite.simulator.network.hardware.nodes.computer import Computer
from primaite.simulator.network.hardware.nodes.server import Server
from primaite.simulator.network.protocols.ftp import FTPCommand, FTPPacket
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.services.ftp.ftp_client import FTPClient
from primaite.simulator.system.services.ftp.ftp_server import FTPServer


@pytest.fixture(scope="function")
def ftp_server() -> Node:
    node = Server(
        hostname="ftp_server", ip_address="192.168.1.10", subnet_mask="255.255.255.0", default_gateway="192.168.1.1"
    )
    node.software_manager.install(software_class=FTPServer)
    node.software_manager.software["FTPServer"].start()
    return node


@pytest.fixture(scope="function")
def ftp_client() -> Node:
    node = Computer(
        hostname="ftp_client", ip_address="192.168.1.11", subnet_mask="255.255.255.0", default_gateway="192.168.1.1"
    )
    return node


def test_create_ftp_server(ftp_server):
    assert ftp_server is not None
    ftp_server_service: FTPServer = ftp_server.software_manager.software["FTPServer"]
    assert ftp_server_service.name is "FTPServer"
    assert ftp_server_service.port is Port.FTP
    assert ftp_server_service.protocol is IPProtocol.TCP


def test_create_ftp_client(ftp_client):
    assert ftp_client is not None
    ftp_client_service: FTPClient = ftp_client.software_manager.software["FTPClient"]
    assert ftp_client_service.name is "FTPClient"
    assert ftp_client_service.port is Port.FTP
    assert ftp_client_service.protocol is IPProtocol.TCP


def test_ftp_server_store_file(ftp_server):
    """Test to make sure the FTP Server knows how to deal with request responses."""
    assert ftp_server.file_system.get_file(folder_name="downloads", file_name="file.txt") is None

    response: FTPPacket = FTPPacket(
        ftp_command=FTPCommand.STOR,
        ftp_command_args={
            "dest_folder_name": "downloads",
            "dest_file_name": "file.txt",
            "file_size": 24,
        },
        packet_payload_size=24,
    )

    ftp_server_service: FTPServer = ftp_server.software_manager.software["FTPServer"]
    ftp_server_service.receive(response)

    assert ftp_server.file_system.get_file(folder_name="downloads", file_name="file.txt")


def test_ftp_client_store_file(ftp_client):
    """Test to make sure the FTP Client knows how to deal with request responses."""
    assert ftp_client.file_system.get_file(folder_name="downloads", file_name="file.txt") is None

    response: FTPPacket = FTPPacket(
        ftp_command=FTPCommand.STOR,
        ftp_command_args={
            "dest_folder_name": "downloads",
            "dest_file_name": "file.txt",
            "file_size": 24,
        },
        packet_payload_size=24,
    )

    ftp_client_service: FTPClient = ftp_client.software_manager.software["FTPClient"]
    ftp_client_service.receive(response)

    assert ftp_client.file_system.get_file(folder_name="downloads", file_name="file.txt")
