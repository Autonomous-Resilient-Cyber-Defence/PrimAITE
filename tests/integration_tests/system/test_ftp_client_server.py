from ipaddress import IPv4Address

from src.primaite.simulator.network.hardware.nodes.computer import Computer
from src.primaite.simulator.network.hardware.nodes.server import Server
from src.primaite.simulator.system.services.ftp.ftp_client import FTPClient
from src.primaite.simulator.system.services.ftp.ftp_server import FTPServer
from src.primaite.simulator.system.services.service import ServiceOperatingState


def test_ftp_client_store_file_in_server(uc2_network):
    """
    Test checks to see if the client is able to store files in the backup server.
    """
    client_1: Computer = uc2_network.get_node_by_hostname("client_1")
    backup_server: Server = uc2_network.get_node_by_hostname("backup_server")

    ftp_client: FTPClient = client_1.software_manager.software["FTPClient"]
    ftp_server: FTPServer = backup_server.software_manager.software["FTPServer"]

    assert ftp_client.operating_state == ServiceOperatingState.RUNNING
    assert ftp_server.operating_state == ServiceOperatingState.RUNNING

    # create file on ftp client
    ftp_client.file_system.create_file(file_name="test_file.txt")

    assert ftp_client.send_file(
        src_folder_name="root",
        src_file_name="test_file.txt",
        dest_folder_name="client_1_backup",
        dest_file_name="test_file.txt",
        dest_ip_address=backup_server.nics.get(next(iter(backup_server.nics))).ip_address,
    )

    assert ftp_server.file_system.get_file(folder_name="client_1_backup", file_name="test_file.txt")


def test_ftp_client_retrieve_file_from_server(uc2_network):
    """
    Test checks to see if the client is able to retrieve files from the backup server.
    """
    client_1: Computer = uc2_network.get_node_by_hostname("client_1")
    backup_server: Server = uc2_network.get_node_by_hostname("backup_server")

    ftp_client: FTPClient = client_1.software_manager.software["FTPClient"]
    ftp_server: FTPServer = backup_server.software_manager.software["FTPServer"]

    assert ftp_client.operating_state == ServiceOperatingState.RUNNING
    assert ftp_server.operating_state == ServiceOperatingState.RUNNING

    # create file on ftp server
    ftp_server.file_system.create_file(file_name="test_file.txt", folder_name="file_share")

    assert ftp_client.request_file(
        src_folder_name="file_share",
        src_file_name="test_file.txt",
        dest_folder_name="downloads",
        dest_file_name="test_file.txt",
        dest_ip_address=backup_server.nics.get(next(iter(backup_server.nics))).ip_address,
    )

    # client should have retrieved the file
    assert ftp_client.file_system.get_file(folder_name="downloads", file_name="test_file.txt")
