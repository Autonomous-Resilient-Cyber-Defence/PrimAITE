# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from ipaddress import IPv4Address

import pytest

from primaite.simulator.file_system.file_system_item_abc import FileSystemItemHealthStatus
from primaite.simulator.network.hardware.base import Node
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.protocols.ftp import FTPCommand, FTPPacket, FTPStatusCode
from primaite.simulator.system.services.ftp.ftp_client import FTPClient
from primaite.simulator.system.services.service import ServiceOperatingState
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.port import PORT_LOOKUP


@pytest.fixture(scope="function")
def ftp_client() -> Node:
    node_cfg = {
        "type": "computer",
        "hostname": "ftp_client",
        "ip_address": "192.168.1.11",
        "subnet_mask": "255.255.255.0",
        "default_gateway": "192.168.1.1",
        "start_up_duration": 0,
    }
    node = Computer.from_config(config=node_cfg)
    node.power_on()
    return node


def test_create_ftp_client(ftp_client):
    assert ftp_client is not None
    ftp_client_service: FTPClient = ftp_client.software_manager.software.get("ftp-client")
    assert ftp_client_service.name == "ftp-client"
    assert ftp_client_service.port is PORT_LOOKUP["FTP"]
    assert ftp_client_service.protocol is PROTOCOL_LOOKUP["TCP"]


def test_ftp_client_store_file(ftp_client):
    """Test to make sure the FTP Client knows how to deal with request responses."""
    assert ftp_client.file_system.get_file(folder_name="downloads", file_name="file.txt") is None

    response: FTPPacket = FTPPacket(
        ftp_command=FTPCommand.STOR,
        ftp_command_args={
            "dest_folder_name": "downloads",
            "dest_file_name": "file.txt",
            "file_size": 24,
            "health_status": FileSystemItemHealthStatus.GOOD,
        },
        packet_payload_size=24,
        status_code=FTPStatusCode.OK,
    )

    ftp_client_service: FTPClient = ftp_client.software_manager.software.get("ftp-client")
    ftp_client_service.receive(response)

    assert ftp_client.file_system.get_file(folder_name="downloads", file_name="file.txt")


def test_ftp_should_not_process_commands_if_service_not_running(ftp_client):
    """Method _process_ftp_command should return false if service is not running."""
    payload: FTPPacket = FTPPacket(
        ftp_command=FTPCommand.PORT,
        ftp_command_args=PORT_LOOKUP["FTP"],
        status_code=FTPStatusCode.OK,
    )

    ftp_client_service: FTPClient = ftp_client.software_manager.software.get("ftp-client")
    ftp_client_service.stop()
    assert ftp_client_service.operating_state is ServiceOperatingState.STOPPED
    assert ftp_client_service._process_ftp_command(payload=payload).status_code is FTPStatusCode.ERROR


def test_ftp_tries_to_senf_file__that_does_not_exist(ftp_client):
    """Method send_file should return false if no file to send."""
    assert ftp_client.file_system.get_file(folder_name="root", file_name="test.txt") is None

    ftp_client_service: FTPClient = ftp_client.software_manager.software.get("ftp-client")
    assert ftp_client_service.operating_state is ServiceOperatingState.RUNNING
    assert (
        ftp_client_service.send_file(
            dest_ip_address=IPv4Address("192.168.1.1"),
            src_folder_name="root",
            src_file_name="test.txt",
            dest_folder_name="root",
            dest_file_name="text.txt",
        )
        is False
    )


def test_offline_ftp_client_receives_request(ftp_client):
    """Receive should return false if the node the ftp client is installed on is offline."""
    ftp_client_service: FTPClient = ftp_client.software_manager.software.get("ftp-client")
    ftp_client.power_off()

    for i in range(ftp_client.config.shut_down_duration + 1):
        ftp_client.apply_timestep(timestep=i)

    assert ftp_client.operating_state is NodeOperatingState.OFF
    assert ftp_client_service.operating_state is ServiceOperatingState.STOPPED

    payload: FTPPacket = FTPPacket(
        ftp_command=FTPCommand.PORT,
        ftp_command_args=PORT_LOOKUP["FTP"],
        status_code=FTPStatusCode.OK,
    )

    assert ftp_client_service.receive(payload=payload) is False


def test_receive_should_fail_if_payload_is_not_ftp(ftp_client):
    """Receive should return false if the node the ftp client is installed on is not an FTPPacket."""
    ftp_client_service: FTPClient = ftp_client.software_manager.software.get("ftp-client")
    assert ftp_client_service.receive(payload=None) is False


def test_receive_should_ignore_payload_with_none_status_code(ftp_client):
    """Receive should ignore payload with no set status code to prevent infinite send/receive loops."""
    payload: FTPPacket = FTPPacket(
        ftp_command=FTPCommand.PORT,
        ftp_command_args=PORT_LOOKUP["FTP"],
        status_code=None,
    )
    ftp_client_service: FTPClient = ftp_client.software_manager.software.get("ftp-client")
    assert ftp_client_service.receive(payload=payload) is False
