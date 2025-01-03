# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.networks import multi_lan_internet_network_example
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.applications.web_browser import WebBrowser
from primaite.simulator.system.services.dns.dns_client import DNSClient
from primaite.simulator.system.services.ftp.ftp_client import FTPClient


def test_all_with_configured_dns_server_ip_can_resolve_url():
    network = multi_lan_internet_network_example()

    for node in network.nodes.values():
        dns_client: DNSClient = node.software_manager.software.get("DNSClient")

        if not dns_client:
            continue

        if dns_client.dns_server:
            assert dns_client.check_domain_exists("sometech.ai")


def test_external_pcs_can_access_sometech_website():
    network = multi_lan_internet_network_example()

    pc_1_browser: WebBrowser = network.get_node_by_hostname("pc_1").software_manager.software["WebBrowser"]
    pc_2_browser: WebBrowser = network.get_node_by_hostname("pc_2").software_manager.software["WebBrowser"]

    assert pc_1_browser.get_webpage()
    assert pc_2_browser.get_webpage()


def test_external_pcs_cannot_access_sometech_db():
    network = multi_lan_internet_network_example()

    pc_1_db_client: DatabaseClient = network.get_node_by_hostname("pc_1").software_manager.software["DatabaseClient"]
    pc_2_db_client: DatabaseClient = network.get_node_by_hostname("pc_2").software_manager.software["DatabaseClient"]

    assert not pc_1_db_client.get_new_connection()
    assert not pc_2_db_client.get_new_connection()


def test_external_pcs_cannot_access_ftp_on_sometech_storage_server():
    network = multi_lan_internet_network_example()

    some_tech_storage_srv = network.get_node_by_hostname("some_tech_storage_srv")
    some_tech_storage_srv.file_system.create_file(file_name="test.png")

    pc_1_ftp_client: FTPClient = network.get_node_by_hostname("pc_1").software_manager.software["FTPClient"]
    pc_2_ftp_client: FTPClient = network.get_node_by_hostname("pc_2").software_manager.software["FTPClient"]

    assert not pc_1_ftp_client.request_file(
        dest_ip_address=some_tech_storage_srv.network_interface[1].ip_address,
        src_folder_name="root",
        src_file_name="test.png",
        dest_folder_name="root",
        dest_file_name="test.png",
    )

    assert not pc_2_ftp_client.request_file(
        dest_ip_address=some_tech_storage_srv.network_interface[1].ip_address,
        src_folder_name="root",
        src_file_name="test.png",
        dest_folder_name="root",
        dest_file_name="test.png",
    )


def test_sometech_webserver_can_access_sometech_db_server():
    network = multi_lan_internet_network_example()

    web_db_client: DatabaseClient = network.get_node_by_hostname("some_tech_web_srv").software_manager.software[
        "DatabaseClient"
    ]

    assert web_db_client.get_new_connection()


def test_sometech_webserver_cannot_access_ftp_on_sometech_storage_server():
    network = multi_lan_internet_network_example()

    some_tech_storage_srv = network.get_node_by_hostname("some_tech_storage_srv")
    some_tech_storage_srv.file_system.create_file(file_name="test.png")

    web_server: Server = network.get_node_by_hostname("some_tech_web_srv")
    web_server.software_manager.install(FTPClient)
    web_ftp_client: FTPClient = web_server.software_manager.software["FTPClient"]

    assert not web_ftp_client.request_file(
        dest_ip_address=some_tech_storage_srv.network_interface[1].ip_address,
        src_folder_name="root",
        src_file_name="test.png",
        dest_folder_name="root",
        dest_file_name="test.png",
    )


def test_sometech_dev_pcs_can_access_sometech_website():
    network = multi_lan_internet_network_example()

    some_tech_snr_dev_pc: Computer = network.get_node_by_hostname("some_tech_snr_dev_pc")

    snr_dev_browser: WebBrowser = some_tech_snr_dev_pc.software_manager.software["WebBrowser"]

    assert snr_dev_browser.get_webpage()

    some_tech_jnr_dev_pc: Computer = network.get_node_by_hostname("some_tech_jnr_dev_pc")

    jnr_dev_browser: WebBrowser = some_tech_jnr_dev_pc.software_manager.software["WebBrowser"]

    assert jnr_dev_browser.get_webpage()


def test_sometech_dev_pcs_can_connect_to_sometech_db_server():
    network = multi_lan_internet_network_example()

    some_tech_snr_dev_pc: Computer = network.get_node_by_hostname("some_tech_snr_dev_pc")
    snr_dev_db_client: DatabaseClient = some_tech_snr_dev_pc.software_manager.software["DatabaseClient"]

    assert snr_dev_db_client.get_new_connection()

    some_tech_jnr_dev_pc: Computer = network.get_node_by_hostname("some_tech_jnr_dev_pc")
    jnr_dev_db_client: DatabaseClient = some_tech_jnr_dev_pc.software_manager.software["DatabaseClient"]

    assert jnr_dev_db_client.get_new_connection()


def test_sometech_snr_dev_can_access_ftp_on_sometech_storage_server():
    network = multi_lan_internet_network_example()

    some_tech_storage_srv = network.get_node_by_hostname("some_tech_storage_srv")
    some_tech_storage_srv.file_system.create_file(file_name="test.png")

    some_tech_snr_dev_pc: Computer = network.get_node_by_hostname("some_tech_snr_dev_pc")
    snr_dev_ftp_client: FTPClient = some_tech_snr_dev_pc.software_manager.software["FTPClient"]

    assert snr_dev_ftp_client.request_file(
        dest_ip_address=some_tech_storage_srv.network_interface[1].ip_address,
        src_folder_name="root",
        src_file_name="test.png",
        dest_folder_name="root",
        dest_file_name="test.png",
    )


def test_sometech_jnr_dev_cannot_access_ftp_on_sometech_storage_server():
    network = multi_lan_internet_network_example()

    some_tech_storage_srv = network.get_node_by_hostname("some_tech_storage_srv")
    some_tech_storage_srv.file_system.create_file(file_name="test.png")

    some_tech_jnr_dev_pc: Computer = network.get_node_by_hostname("some_tech_jnr_dev_pc")
    jnr_dev_ftp_client: FTPClient = some_tech_jnr_dev_pc.software_manager.software["FTPClient"]

    assert not jnr_dev_ftp_client.request_file(
        dest_ip_address=some_tech_storage_srv.network_interface[1].ip_address,
        src_folder_name="root",
        src_file_name="test.png",
        dest_folder_name="root",
        dest_file_name="test.png",
    )


def test_sometech_hr_pc_can_access_sometech_website():
    network = multi_lan_internet_network_example()

    some_tech_hr_pc: Computer = network.get_node_by_hostname("some_tech_hr_1")

    hr_browser: WebBrowser = some_tech_hr_pc.software_manager.software["WebBrowser"]

    assert hr_browser.get_webpage()


def test_sometech_hr_pc_cannot_access_sometech_db():
    network = multi_lan_internet_network_example()

    some_tech_hr_pc: Computer = network.get_node_by_hostname("some_tech_hr_1")

    hr_db_client: DatabaseClient = some_tech_hr_pc.software_manager.software["DatabaseClient"]

    assert not hr_db_client.get_new_connection()


def test_sometech_hr_pc_cannot_access_ftp_on_sometech_storage_server():
    network = multi_lan_internet_network_example()

    some_tech_storage_srv = network.get_node_by_hostname("some_tech_storage_srv")
    some_tech_storage_srv.file_system.create_file(file_name="test.png")

    some_tech_hr_pc: Computer = network.get_node_by_hostname("some_tech_hr_1")
    hr_ftp_client: FTPClient = some_tech_hr_pc.software_manager.software["FTPClient"]

    assert not hr_ftp_client.request_file(
        dest_ip_address=some_tech_storage_srv.network_interface[1].ip_address,
        src_folder_name="root",
        src_file_name="test.png",
        dest_folder_name="root",
        dest_file_name="test.png",
    )
