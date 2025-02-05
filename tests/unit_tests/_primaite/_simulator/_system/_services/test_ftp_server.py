# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
import pytest

from primaite.simulator.file_system.file_system_item_abc import FileSystemItemHealthStatus
from primaite.simulator.network.hardware.base import Node
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.protocols.ftp import FTPCommand, FTPPacket, FTPStatusCode
from primaite.simulator.system.services.ftp.ftp_server import FTPServer
from primaite.simulator.system.services.service import ServiceOperatingState
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.port import PORT_LOOKUP


@pytest.fixture(scope="function")
def ftp_server() -> Node:
    node_cfg = {
        "type": "server",
        "hostname": "ftp_server",
        "ip_address": "192.168.1.10",
        "subnet_mask": "255.255.255.0",
        "default_gateway": "192.168.1.1",
        "start_up_duration": 0,
    }
    node = Server.from_config(config=node_cfg)
    node.power_on()
    node.software_manager.install(software_class=FTPServer)
    return node


def test_create_ftp_server(ftp_server):
    assert ftp_server is not None
    ftp_server_service: FTPServer = ftp_server.software_manager.software.get("ftp-server")
    assert ftp_server_service.name == "ftp-server"
    assert ftp_server_service.port is PORT_LOOKUP["FTP"]
    assert ftp_server_service.protocol is PROTOCOL_LOOKUP["TCP"]


def test_ftp_server_store_file(ftp_server):
    """Test to make sure the FTP Server knows how to deal with request responses."""
    assert ftp_server.file_system.get_file(folder_name="downloads", file_name="file.txt") is None

    response: FTPPacket = FTPPacket(
        ftp_command=FTPCommand.STOR,
        ftp_command_args={
            "dest_folder_name": "downloads",
            "dest_file_name": "file.txt",
            "file_size": 24,
            "health_status": FileSystemItemHealthStatus.GOOD,
        },
        packet_payload_size=24,
    )

    ftp_server_service: FTPServer = ftp_server.software_manager.software.get("ftp-server")
    ftp_server_service.receive(response)

    assert ftp_server.file_system.get_file(folder_name="downloads", file_name="file.txt")


def test_ftp_server_should_send_error_if_port_arg_is_invalid(ftp_server):
    """Should fail if the port command receives an invalid port."""
    payload: FTPPacket = FTPPacket(
        ftp_command=FTPCommand.PORT,
        ftp_command_args=None,
        packet_payload_size=24,
    )

    ftp_server_service: FTPServer = ftp_server.software_manager.software.get("ftp-server")
    assert ftp_server_service._process_ftp_command(payload=payload).status_code is FTPStatusCode.ERROR


def test_ftp_server_receives_non_ftp_packet(ftp_server):
    """Receive should return false if the service receives a non ftp packet."""
    response: FTPPacket = None

    ftp_server_service: FTPServer = ftp_server.software_manager.software.get("ftp-server")
    assert ftp_server_service.receive(response) is False


def test_offline_ftp_server_receives_request(ftp_server):
    """Receive should return false if the service is stopped."""
    response: FTPPacket = FTPPacket(
        ftp_command=FTPCommand.STOR,
        ftp_command_args={
            "dest_folder_name": "downloads",
            "dest_file_name": "file.txt",
            "file_size": 24,
        },
        packet_payload_size=24,
    )

    ftp_server_service: FTPServer = ftp_server.software_manager.software.get("ftp-server")
    ftp_server_service.stop()
    assert ftp_server_service.operating_state is ServiceOperatingState.STOPPED
    assert ftp_server_service.receive(response) is False
