from ipaddress import IPv4Address

import pytest

from primaite.simulator.network.hardware.base import Node
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.services.ftp.ftp_client import FTPClient
from primaite.simulator.system.services.ftp.ftp_server import FTPServer


@pytest.fixture(scope="function")
def ftp_server() -> Node:
    node = Node(hostname="ftp_server")
    node.software_manager.install(software_class=FTPServer)
    node.software_manager.software["FTPServer"].start()
    return node


@pytest.fixture(scope="function")
def ftp_client() -> Node:
    node = Node(hostname="ftp_client")
    node.software_manager.install(software_class=FTPClient)
    node.software_manager.software["FTPClient"].start()
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
