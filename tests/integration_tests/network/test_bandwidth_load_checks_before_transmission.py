# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from primaite.simulator.file_system.file_type import FileType
from primaite.simulator.network.hardware.nodes.network.router import ACLAction
from primaite.simulator.system.services.ftp.ftp_client import FTPClient
from primaite.simulator.system.services.ftp.ftp_server import FTPServer
from tests.integration_tests.network.test_wireless_router import wireless_wan_network
from tests.integration_tests.system.test_ftp_client_server import ftp_client_and_ftp_server


def test_wireless_link_loading(wireless_wan_network):
    client, server, router_1, router_2 = wireless_wan_network

    # Configure Router 1 ACLs
    router_1.acl.add_rule(action=ACLAction.PERMIT, position=1)

    # Configure Router 2 ACLs
    router_2.acl.add_rule(action=ACLAction.PERMIT, position=1)

    airspace = router_1.config.airspace

    client.software_manager.install(FTPClient)
    ftp_client: FTPClient = client.software_manager.software.get("FTPClient")
    ftp_client.start()

    server.software_manager.install(FTPServer)
    ftp_server: FTPServer = server.software_manager.software.get("FTPServer")
    ftp_server.start()

    client.file_system.create_file(file_name="mixtape", size=10 * 10**6, file_type=FileType.MP3, folder_name="music")

    assert ftp_client.send_file(
        src_file_name="mixtape.mp3",
        src_folder_name="music",
        dest_ip_address=server.network_interface[1].ip_address,
        dest_file_name="mixtape.mp3",
        dest_folder_name="music",
    )

    # Reset the physical links between the host nodes and the routers
    client.network_interface[1]._connected_link.pre_timestep(1)
    server.network_interface[1]._connected_link.pre_timestep(1)

    assert not ftp_client.send_file(
        src_file_name="mixtape.mp3",
        src_folder_name="music",
        dest_ip_address=server.network_interface[1].ip_address,
        dest_file_name="mixtape3.mp3",
        dest_folder_name="music",
    )

    # Reset the physical links between the host nodes and the routers
    client.network_interface[1]._connected_link.pre_timestep(1)
    server.network_interface[1]._connected_link.pre_timestep(1)

    airspace.reset_bandwidth_load()

    assert ftp_client.send_file(
        src_file_name="mixtape.mp3",
        src_folder_name="music",
        dest_ip_address=server.network_interface[1].ip_address,
        dest_file_name="mixtape3.mp3",
        dest_folder_name="music",
    )


def test_wired_link_loading(ftp_client_and_ftp_server):
    ftp_client, computer, ftp_server, server = ftp_client_and_ftp_server

    link = computer.network_interface[1]._connected_link  # noqa

    assert link.is_up

    link.pre_timestep(1)

    computer.file_system.create_file(
        file_name="mixtape", size=10 * 10**6, file_type=FileType.MP3, folder_name="music"
    )
    link_load = link.current_load
    assert link_load == 0.0

    assert ftp_client.send_file(
        src_file_name="mixtape.mp3",
        src_folder_name="music",
        dest_ip_address=server.network_interface[1].ip_address,
        dest_file_name="mixtape.mp3",
        dest_folder_name="music",
    )

    new_link_load = link.current_load
    assert new_link_load > link_load

    assert not ftp_client.send_file(
        src_file_name="mixtape.mp3",
        src_folder_name="music",
        dest_ip_address=server.network_interface[1].ip_address,
        dest_file_name="mixtape1.mp3",
        dest_folder_name="music",
    )

    link.pre_timestep(2)

    link_load = link.current_load
    assert link_load == 0.0

    assert ftp_client.send_file(
        src_file_name="mixtape.mp3",
        src_folder_name="music",
        dest_ip_address=server.network_interface[1].ip_address,
        dest_file_name="mixtape1.mp3",
        dest_folder_name="music",
    )

    new_link_load = link.current_load
    assert new_link_load > link_load
