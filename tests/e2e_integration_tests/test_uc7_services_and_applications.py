# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

import pytest
import yaml

from primaite.config.load import _EXAMPLE_CFG
from primaite.game.game import PrimaiteGame
from primaite.session.environment import PrimaiteGymEnv
from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.system.applications.application import ApplicationOperatingState
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.applications.web_browser import WebBrowser
from primaite.simulator.system.services.database.database_service import DatabaseService
from primaite.simulator.system.services.dns.dns_client import DNSClient
from primaite.simulator.system.services.dns.dns_server import DNSServer
from primaite.simulator.system.services.ftp.ftp_client import FTPClient
from primaite.simulator.system.services.ftp.ftp_server import FTPServer
from primaite.simulator.system.services.ntp.ntp_client import NTPClient
from primaite.simulator.system.services.ntp.ntp_server import NTPServer
from primaite.simulator.system.services.service import ServiceOperatingState
from primaite.simulator.system.software import SoftwareHealthState

CONFIG_FILE = _EXAMPLE_CFG / "uc7_config.yaml"


@pytest.fixture(scope="function")
def uc7_network() -> Network:
    with open(file=CONFIG_FILE, mode="r") as f:
        cfg = yaml.safe_load(stream=f)

    game = PrimaiteGame.from_config(cfg=cfg)
    return game.simulation.network


def assert_ntp_client(host):
    """Confirms that the ntp_client service is present and functioning."""
    ntp_client: NTPClient = host.software_manager.software["ntp-client"]
    assert ntp_client is not None
    assert ntp_client.operating_state == ServiceOperatingState.RUNNING
    assert ntp_client.health_state_actual == SoftwareHealthState.GOOD


def assert_dns_client(host):
    """Confirms that the dns_client service is present and functioning."""
    dns_client: DNSClient = host.software_manager.software["dns-client"]
    assert dns_client is not None
    assert dns_client.operating_state == ServiceOperatingState.RUNNING
    assert dns_client.health_state_actual == SoftwareHealthState.GOOD


def assert_web_browser(host: Computer):
    """Asserts that the web_browser application is present and functioning."""
    web_browser: WebBrowser = host.software_manager.software["web-browser"]
    assert web_browser is not None
    assert web_browser.operating_state == ApplicationOperatingState.RUNNING
    assert web_browser.health_state_actual == SoftwareHealthState.GOOD


def assert_database_client(host: Computer):
    """Asserts that the database_client application is present and functioning."""
    database_client = host.software_manager.software["database-client"]
    assert database_client is not None
    assert database_client.operating_state == ApplicationOperatingState.RUNNING
    assert database_client.health_state_actual == SoftwareHealthState.GOOD


def test_home_office_software(uc7_network):
    """Asserts that each host in the home_office network contains the expected software."""
    network: Network = uc7_network
    home_pub_pc_1: Computer = network.get_node_by_hostname("HOME-PUB-PC-1")
    home_pub_pc_2: Computer = network.get_node_by_hostname("HOME-PUB-PC-1")
    home_pub_srv: Server = network.get_node_by_hostname("HOME-PUB-SRV")

    # Home Office PC 1
    assert_web_browser(home_pub_pc_1)
    assert_database_client(home_pub_pc_1)
    assert_dns_client(home_pub_pc_1)
    assert_ntp_client(home_pub_pc_1)

    # Home Office PC 2
    assert_web_browser(home_pub_pc_2)
    assert_database_client(home_pub_pc_2)
    assert_dns_client(home_pub_pc_2)
    assert_ntp_client(home_pub_pc_2)

    # Home Office Server
    assert_dns_client(home_pub_srv)
    assert_ntp_client(home_pub_srv)


def test_internet_dns_server(uc7_network):
    """Asserts that `ISP-PUB-SRV-DNS` host's DNSServer application is operating and functioning as expected."""
    network: Network = uc7_network
    isp_pub_srv_dns: Server = network.get_node_by_hostname("ISP-PUB-SRV-DNS")

    # Confirming that the DNSServer is up and running:

    dns_server: DNSServer = isp_pub_srv_dns.software_manager.software["dns-server"]
    assert dns_server is not None
    assert dns_server.operating_state == ServiceOperatingState.RUNNING
    assert dns_server.health_state_actual == SoftwareHealthState.GOOD

    # Confirming that the DNSServer is performing as expected by performing a request from a client

    home_pub_pc_1: Computer = network.get_node_by_hostname("HOME-PUB-PC-1")
    dns_client: DNSClient = home_pub_pc_1.software_manager.software["dns-client"]

    assert dns_client.check_domain_exists(target_domain="some_tech.com")
    assert dns_client.dns_cache.get("some_tech.com", None) is not None
    assert len(dns_client.dns_cache) == 1


def test_remote_office_software(uc7_network):
    """Asserts that each host on the remote_office network has the expected services & applications which are operating as expected."""
    network = uc7_network
    rem_pub_pc_1: Computer = network.get_node_by_hostname(hostname="REM-PUB-PC-1")
    rem_pub_pc_2: Computer = network.get_node_by_hostname(hostname="REM-PUB-PC-2")
    rem_pub_srv: Server = network.get_node_by_hostname(hostname="REM-PUB-SRV")

    # Remote Site PC 1
    assert_web_browser(rem_pub_pc_1)
    assert_database_client(rem_pub_pc_1)
    assert_dns_client(rem_pub_pc_1)
    assert_ntp_client(rem_pub_pc_1)

    # Remote Site PC 2
    assert_web_browser(rem_pub_pc_2)
    assert_database_client(rem_pub_pc_2)
    assert_dns_client(rem_pub_pc_2)
    assert_ntp_client(rem_pub_pc_2)

    # Remote Site Server
    assert_dns_client(rem_pub_srv)
    assert_ntp_client(rem_pub_srv)


def test_dmz_web_server(uc7_network):
    """Asserts that the DMZ WebServer functions as expected"""
    network: Network = uc7_network
    st_dmz_pub_srv_web: Server = network.get_node_by_hostname("ST_DMZ-PUB-SRV-WEB")

    # Asserting the ST Web Server is working as expected
    st_web_server = st_dmz_pub_srv_web.software_manager.software["web-server"]
    assert st_web_server is not None
    assert st_web_server.operating_state == ServiceOperatingState.RUNNING
    assert st_web_server.health_state_actual == SoftwareHealthState.GOOD

    # Asserting that WebBrowser can actually connect to the WebServer

    # SOME TECH Human Resources --> DMZ Web Server
    st_hr_pc_1: Computer = network.get_node_by_hostname("ST_HR-PRV-PC-1")
    st_hr_pc_1_web_browser: WebBrowser = st_hr_pc_1.software_manager.software["web-browser"]
    assert st_hr_pc_1_web_browser.get_webpage("http://some_tech.com")

    # Remote Site --> DMZ Web Server
    rem_pub_pc_1: Computer = network.get_node_by_hostname("REM-PUB-PC-1")
    rem_pub_pc_1_web_browser: WebBrowser = rem_pub_pc_1.software_manager.software["web-browser"]
    assert rem_pub_pc_1_web_browser.get_webpage("http://some_tech.com")

    # Home Office --> DMZ Web Server
    home_pub_pc_1: Computer = network.get_node_by_hostname("HOME-PUB-PC-1")
    home_pub_pc_1_web_browser: WebBrowser = home_pub_pc_1.software_manager.software["web-browser"]
    assert home_pub_pc_1_web_browser.get_webpage("http://some_tech.com")


def test_tech_head_office_software(uc7_network):
    """Asserts that each host on the some_tech_head_office network has the expected services & applications which are operating as expected."""
    network: Network = uc7_network

    st_head_office_private_pc_1: Computer = network.get_node_by_hostname("ST_HO-PRV-PC-1")
    st_head_office_private_pc_2: Computer = network.get_node_by_hostname("ST_HO-PRV-PC-2")
    st_head_office_private_pc_3: Computer = network.get_node_by_hostname("ST_HO-PRV-PC-3")

    # ST Head Office One

    assert_web_browser(st_head_office_private_pc_1)
    assert_database_client(st_head_office_private_pc_1)
    assert_dns_client(st_head_office_private_pc_1)
    assert_ntp_client(st_head_office_private_pc_1)

    # ST Head Office Two

    assert_web_browser(st_head_office_private_pc_2)
    assert_database_client(st_head_office_private_pc_2)
    assert_dns_client(st_head_office_private_pc_2)
    assert_ntp_client(st_head_office_private_pc_2)

    # ST Head Office Three

    assert_web_browser(st_head_office_private_pc_3)
    assert_database_client(st_head_office_private_pc_3)
    assert_dns_client(st_head_office_private_pc_3)
    assert_ntp_client(st_head_office_private_pc_3)


def test_tech_human_resources_office_software(uc7_network):
    """Asserts that each host on the some_tech human_resources network has the expected services & applications which are operating as expected."""
    network: Network = uc7_network

    st_hr_pc_1: Computer = network.get_node_by_hostname("ST_HR-PRV-PC-1")
    st_hr_pc_2: Computer = network.get_node_by_hostname("ST_HR-PRV-PC-2")
    st_hr_pc_3: Computer = network.get_node_by_hostname("ST_HR-PRV-PC-3")

    # ST Human Resource PC 1

    assert_web_browser(st_hr_pc_1)
    assert_database_client(st_hr_pc_1)
    assert_dns_client(st_hr_pc_1)
    assert_ntp_client(st_hr_pc_1)

    # ST Human Resource PC 2

    assert_web_browser(st_hr_pc_2)
    assert_database_client(st_hr_pc_2)
    assert_dns_client(st_hr_pc_2)
    assert_ntp_client(st_hr_pc_2)

    # ST Human Resource PC 3

    assert_web_browser(st_hr_pc_3)
    assert_database_client(st_hr_pc_3)
    assert_dns_client(st_hr_pc_3)
    assert_ntp_client(st_hr_pc_3)


def test_tech_data_software(uc7_network):
    """Asserts the database and database storage servers on the some_tech data network are operating as expected."""
    network: Network = uc7_network
    st_data_database_server: Server = network.get_node_by_hostname("ST_DATA-PRV-SRV-DB")
    st_data_database_storage: Server = network.get_node_by_hostname("ST_DATA-PRV-SRV-STORAGE")
    st_proj_a_pc_1: Computer = network.get_node_by_hostname("ST_PROJ-A-PRV-PC-1")

    # Asserting that the database_service is working as expected
    database_service: DatabaseService = st_data_database_server.software_manager.software["database-service"]

    assert database_service is not None
    assert database_service.operating_state == ServiceOperatingState.RUNNING
    assert database_service.health_state_actual == SoftwareHealthState.GOOD

    # Asserting that the database_client can connect to the database
    database_client: DatabaseClient = st_proj_a_pc_1.software_manager.software["database-client"]

    assert database_client.server_ip_address is not None
    assert database_client.server_ip_address == st_data_database_server.network_interface[1].ip_address
    assert database_client.connect()

    # Asserting that the database storage works as expected.
    assert database_service.backup_server_ip == st_data_database_storage.network_interface[1].ip_address
    assert database_service.backup_database()


def test_tech_proj_a_software(uc7_network):
    """Asserts that each host on the some_tech project A network has the expected services & applications which are operating as expected."""
    network: Network = uc7_network
    st_proj_a_pc_1: Computer = network.get_node_by_hostname("ST_PROJ-A-PRV-PC-1")
    st_proj_a_pc_2: Computer = network.get_node_by_hostname("ST_PROJ-A-PRV-PC-2")
    st_proj_a_pc_3: Computer = network.get_node_by_hostname("ST_PROJ-A-PRV-PC-3")

    # ST Project A - PC 1

    assert_web_browser(st_proj_a_pc_1)
    assert_database_client(st_proj_a_pc_1)
    assert_dns_client(st_proj_a_pc_1)
    assert_ntp_client(st_proj_a_pc_1)

    # ST Project A - PC 2

    assert_web_browser(st_proj_a_pc_2)
    assert_database_client(st_proj_a_pc_2)
    assert_dns_client(st_proj_a_pc_2)
    assert_ntp_client(st_proj_a_pc_2)

    # ST Project A - PC 3

    assert_web_browser(st_proj_a_pc_3)
    assert_database_client(st_proj_a_pc_3)
    assert_dns_client(st_proj_a_pc_3)
    assert_ntp_client(st_proj_a_pc_3)


def test_tech_proj_b_software(uc7_network):
    """Asserts that each host on the some_tech project A network has the expected services & applications which are operating as expected."""
    network: Network = uc7_network
    st_proj_b_pc_1: Computer = network.get_node_by_hostname("ST_PROJ-B-PRV-PC-1")
    st_proj_b_pc_2: Computer = network.get_node_by_hostname("ST_PROJ-B-PRV-PC-2")
    st_proj_b_pc_3: Computer = network.get_node_by_hostname("ST_PROJ-B-PRV-PC-3")

    # ST Project B - PC 1

    assert_web_browser(st_proj_b_pc_1)
    assert_database_client(st_proj_b_pc_1)
    assert_dns_client(st_proj_b_pc_1)
    assert_ntp_client(st_proj_b_pc_1)

    # ST Project B - PC2

    assert_web_browser(st_proj_b_pc_2)
    assert_database_client(st_proj_b_pc_2)
    assert_dns_client(st_proj_b_pc_2)
    assert_ntp_client(st_proj_b_pc_2)

    # ST Project B - PC3

    assert_web_browser(st_proj_b_pc_3)
    assert_database_client(st_proj_b_pc_3)
    assert_dns_client(st_proj_b_pc_3)
    assert_ntp_client(st_proj_b_pc_3)


def test_tech_proj_c_software(uc7_network):
    """Asserts that each host on the some_tech project A network has the expected services & applications which are operating as expected."""
    network: Network = uc7_network
    st_proj_c_pc_1: Computer = network.get_node_by_hostname("ST_PROJ-C-PRV-PC-1")
    st_proj_c_pc_2: Computer = network.get_node_by_hostname("ST_PROJ-C-PRV-PC-2")
    st_proj_c_pc_3: Computer = network.get_node_by_hostname("ST_PROJ-C-PRV-PC-3")

    # ST Project C - PC 1

    assert_web_browser(st_proj_c_pc_1)
    assert_database_client(st_proj_c_pc_1)
    assert_dns_client(st_proj_c_pc_1)
    assert_ntp_client(st_proj_c_pc_1)

    # ST Project C - PC2

    assert_web_browser(st_proj_c_pc_2)
    assert_database_client(st_proj_c_pc_2)
    assert_dns_client(st_proj_c_pc_2)
    assert_ntp_client(st_proj_c_pc_2)

    # ST Project C - PC3

    assert_web_browser(st_proj_c_pc_3)
    assert_database_client(st_proj_c_pc_3)
    assert_dns_client(st_proj_c_pc_3)
    assert_ntp_client(st_proj_c_pc_3)
