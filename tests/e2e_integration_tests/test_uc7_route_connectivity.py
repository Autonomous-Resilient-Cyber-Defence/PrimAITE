# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
import pytest
import yaml

from primaite.config.load import _EXAMPLE_CFG
from primaite.game.game import PrimaiteGame
from primaite.session.environment import PrimaiteGymEnv
from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.hardware.nodes.network.firewall import Firewall
from primaite.simulator.network.hardware.nodes.network.router import Router
from primaite.simulator.network.hardware.nodes.network.switch import Switch

CONFIG_FILE = _EXAMPLE_CFG / "uc7_config.yaml"


@pytest.fixture(scope="function")
def uc7_network() -> Network:
    with open(file=CONFIG_FILE, mode="r") as f:
        cfg = yaml.safe_load(stream=f)

    game = PrimaiteGame.from_config(cfg=cfg)
    return game.simulation.network


def test_ping_home_office(uc7_network):
    """Asserts that all home_pub_* can ping each-other and the public dns (isp_pub_srv_dns)"""
    network = uc7_network
    home_pub_pc_1: Computer = network.get_node_by_hostname("HOME-PUB-PC-1")
    home_pub_pc_2: Computer = network.get_node_by_hostname("HOME-PUB-PC-2")
    home_pub_pc_srv: Server = network.get_node_by_hostname("HOME-PUB-SRV")
    home_pub_rt_dr: Router = network.get_node_by_hostname("HOME-PUB-RT-DR")
    isp_pub_srv_dns: Server = network.get_node_by_hostname("ISP-PUB-SRV-DNS")

    assert home_pub_pc_1.ping(isp_pub_srv_dns.network_interface[1].ip_address)

    def ping_all_home_office(host):
        assert host.ping(home_pub_pc_1.network_interface[1].ip_address)
        assert host.ping(home_pub_pc_2.network_interface[1].ip_address)
        assert host.ping(home_pub_pc_srv.network_interface[1].ip_address)
        assert host.ping(home_pub_rt_dr.network_interface[1].ip_address)
        assert host.ping(isp_pub_srv_dns.network_interface[1].ip_address)

    ping_all_home_office(home_pub_pc_1)
    ping_all_home_office(home_pub_pc_2)
    ping_all_home_office(home_pub_pc_srv)
    ping_all_home_office(isp_pub_srv_dns)


def test_ping_remote_site(uc7_network):
    """Asserts that all remote_pub_* hosts can ping each-other and the public dns server (isp_pub_srv_dns)"""
    network = uc7_network
    rem_pub_fw: Firewall = network.get_node_by_hostname(hostname="REM-PUB-FW")
    rem_pub_rt_dr: Router = network.get_node_by_hostname(hostname="REM-PUB-RT-DR")
    rem_pub_pc_1: Computer = network.get_node_by_hostname(hostname="REM-PUB-PC-1")
    rem_pub_pc_2: Computer = network.get_node_by_hostname(hostname="REM-PUB-PC-2")
    rem_pub_srv: Computer = network.get_node_by_hostname(hostname="REM-PUB-SRV")

    def ping_all_remote_site(host):
        assert host.ping(rem_pub_fw.network_interface[1].ip_address)
        assert host.ping(rem_pub_rt_dr.network_interface[1].ip_address)
        assert host.ping(rem_pub_pc_1.network_interface[1].ip_address)
        assert host.ping(rem_pub_pc_2.network_interface[1].ip_address)
        assert host.ping(rem_pub_srv.network_interface[1].ip_address)

    ping_all_remote_site(host=rem_pub_fw)
    ping_all_remote_site(host=rem_pub_rt_dr)
    ping_all_remote_site(host=rem_pub_pc_1)
    ping_all_remote_site(host=rem_pub_pc_2)
    ping_all_remote_site(host=rem_pub_srv)


def test_ping_some_tech_dmz(uc7_network):
    """Asserts that the st_dmz_pub_srv_web and the st_public_firewall can ping each other and remote site and home office."""
    network = uc7_network
    st_pub_fw: Firewall = network.get_node_by_hostname(hostname="ST-PUB-FW")
    st_dmz_pub_srv_web: Server = network.get_node_by_hostname(hostname="ST-DMZ-PUB-SRV-WEB")
    isp_pub_srv_dns: Server = network.get_node_by_hostname("ISP-PUB-SRV-DNS")
    home_pub_pc_1: Computer = network.get_node_by_hostname("HOME-PUB-PC-1")

    def ping_all_some_tech_dmz(host):
        assert host.ping(st_dmz_pub_srv_web.network_interface[1].ip_address)
        assert host.ping(isp_pub_srv_dns.network_interface[1].ip_address)

    ping_all_some_tech_dmz(host=st_pub_fw)
    ping_all_some_tech_dmz(host=isp_pub_srv_dns)
    ping_all_some_tech_dmz(host=home_pub_pc_1)


def test_ping_some_tech_head_office(uc7_network):
    """Asserts that all the some_tech_* PCs can ping each other and the public dns"""
    network = uc7_network
    st_home_office_private_pc_1: Computer = network.get_node_by_hostname("ST-HO-PRV-PC-1")
    st_home_office_private_pc_2: Computer = network.get_node_by_hostname("ST-HO-PRV-PC-2")
    st_home_office_private_pc_3: Computer = network.get_node_by_hostname("ST-HO-PRV-PC-3")
    isp_pub_srv_dns: Server = network.get_node_by_hostname("ISP-PUB-SRV-DNS")

    def ping_all_some_tech_head_office(host):
        assert host.ping(st_home_office_private_pc_1.network_interface[1].ip_address)
        assert host.ping(st_home_office_private_pc_2.network_interface[1].ip_address)
        assert host.ping(st_home_office_private_pc_3.network_interface[1].ip_address)
        assert host.ping(isp_pub_srv_dns.network_interface[1].ip_address)

    ping_all_some_tech_head_office(host=st_home_office_private_pc_1)
    ping_all_some_tech_head_office(host=st_home_office_private_pc_2)
    ping_all_some_tech_head_office(host=st_home_office_private_pc_3)


def test_ping_some_tech_hr(uc7_network):
    """Assert that all some_tech_hr_* PCs can ping each other and the public dns"""
    network = uc7_network
    some_tech_hr_pc_1: Computer = network.get_node_by_hostname("ST-HR-PRV-PC-1")
    some_tech_hr_pc_2: Computer = network.get_node_by_hostname("ST-HR-PRV-PC-2")
    some_tech_hr_pc_3: Computer = network.get_node_by_hostname("ST-HR-PRV-PC-3")
    isp_pub_srv_dns: Server = network.get_node_by_hostname("ISP-PUB-SRV-DNS")

    def ping_all_some_tech_hr(host):
        assert host.ping(some_tech_hr_pc_1.network_interface[1].ip_address)
        assert host.ping(some_tech_hr_pc_2.network_interface[1].ip_address)
        assert host.ping(some_tech_hr_pc_3.network_interface[1].ip_address)
        assert host.ping(isp_pub_srv_dns.network_interface[1].ip_address)

    ping_all_some_tech_hr(some_tech_hr_pc_1)
    ping_all_some_tech_hr(some_tech_hr_pc_2)
    ping_all_some_tech_hr(some_tech_hr_pc_3)


def test_some_tech_data_hr(uc7_network):
    """Assert that all some_tech_data_* servers can ping each other and the public dns."""
    network = uc7_network
    some_tech_data_server_storage: Server = network.get_node_by_hostname("ST-DATA-PRV-SRV-STORAGE")
    some_tech_data_server_database: Server = network.get_node_by_hostname("ST-DATA-PRV-SRV-DB")
    isp_pub_srv_dns: Server = network.get_node_by_hostname("ISP-PUB-SRV-DNS")

    def ping_all_some_tech_hr(host):
        assert host.ping(some_tech_data_server_storage.network_interface[1].ip_address)
        assert host.ping(some_tech_data_server_database.network_interface[1].ip_address)
        assert host.ping(isp_pub_srv_dns.network_interface[1].ip_address)

    ping_all_some_tech_hr(some_tech_data_server_storage)
    ping_all_some_tech_hr(some_tech_data_server_database)


def test_some_tech_project_a(uc7_network):
    """Asserts that all some_tech project A's PCs can ping each other and the public dns."""
    network = uc7_network
    some_tech_proj_a_pc_1: Computer = network.get_node_by_hostname("ST-PROJ-A-PRV-PC-1")
    some_tech_proj_a_pc_2: Computer = network.get_node_by_hostname("ST-PROJ-A-PRV-PC-2")
    some_tech_proj_a_pc_3: Computer = network.get_node_by_hostname("ST-PROJ-A-PRV-PC-3")
    isp_pub_srv_dns: Server = network.get_node_by_hostname("ISP-PUB-SRV-DNS")

    def ping_all_some_tech_proj_a(host):
        assert host.ping(some_tech_proj_a_pc_1.network_interface[1].ip_address)
        assert host.ping(some_tech_proj_a_pc_2.network_interface[1].ip_address)
        assert host.ping(some_tech_proj_a_pc_3.network_interface[1].ip_address)
        assert host.ping(isp_pub_srv_dns.network_interface[1].ip_address)

    ping_all_some_tech_proj_a(some_tech_proj_a_pc_1)
    ping_all_some_tech_proj_a(some_tech_proj_a_pc_2)
    ping_all_some_tech_proj_a(some_tech_proj_a_pc_3)


def test_some_tech_project_b(uc7_network):
    """Asserts that all some_tech_project_b PC's can ping each other and the public dps."""
    network = uc7_network
    some_tech_proj_b_pc_1: Computer = network.get_node_by_hostname("ST-PROJ-B-PRV-PC-1")
    some_tech_proj_b_pc_2: Computer = network.get_node_by_hostname("ST-PROJ-B-PRV-PC-2")
    some_tech_proj_b_pc_3: Computer = network.get_node_by_hostname("ST-PROJ-B-PRV-PC-3")
    isp_pub_srv_dns: Server = network.get_node_by_hostname("ISP-PUB-SRV-DNS")

    def ping_all_some_tech_proj_b(host):
        assert host.ping(some_tech_proj_b_pc_1.network_interface[1].ip_address)
        assert host.ping(some_tech_proj_b_pc_2.network_interface[1].ip_address)
        assert host.ping(some_tech_proj_b_pc_3.network_interface[1].ip_address)
        assert host.ping(isp_pub_srv_dns.network_interface[1].ip_address)

    ping_all_some_tech_proj_b(some_tech_proj_b_pc_1)
    ping_all_some_tech_proj_b(some_tech_proj_b_pc_2)
    ping_all_some_tech_proj_b(some_tech_proj_b_pc_3)


def test_some_tech_project_a(uc7_network):
    """Asserts that all some_tech_project_c PC's can ping each other and the public dps."""
    network = uc7_network
    some_tech_proj_c_pc_1: Computer = network.get_node_by_hostname("ST-PROJ-C-PRV-PC-1")
    some_tech_proj_c_pc_2: Computer = network.get_node_by_hostname("ST-PROJ-C-PRV-PC-2")
    some_tech_proj_c_pc_3: Computer = network.get_node_by_hostname("ST-PROJ-C-PRV-PC-3")
    isp_pub_srv_dns: Server = network.get_node_by_hostname("ISP-PUB-SRV-DNS")

    def ping_all_some_tech_proj_c(host):
        assert host.ping(some_tech_proj_c_pc_1.network_interface[1].ip_address)
        assert host.ping(some_tech_proj_c_pc_2.network_interface[1].ip_address)
        assert host.ping(some_tech_proj_c_pc_3.network_interface[1].ip_address)
        assert host.ping(isp_pub_srv_dns.network_interface[1].ip_address)

    ping_all_some_tech_proj_c(some_tech_proj_c_pc_1)
    ping_all_some_tech_proj_c(some_tech_proj_c_pc_2)
    ping_all_some_tech_proj_c(some_tech_proj_c_pc_3)


def test_ping_all_networks(uc7_network):
    """Asserts that one machine from each network is able to ping all others."""
    network = uc7_network
    home_office_pc_1: Computer = network.get_node_by_hostname("HOME-PUB-PC-1")
    isp_pub_srv_dns: Server = network.get_node_by_hostname("ISP-PUB-SRV-DNS")
    remote_office_pc_1: Computer = network.get_node_by_hostname("REM-PUB-PC-1")
    st_head_office_pc_1: Computer = network.get_node_by_hostname("ST-HO-PRV-PC-1")
    st_human_resources_pc_1: Computer = network.get_node_by_hostname("ST-HR-PRV-PC-1")
    st_data_storage_server: Server = network.get_node_by_hostname("ST-DATA-PRV-SRV-STORAGE")
    st_data_database_server: Server = network.get_node_by_hostname("ST-DATA-PRV-SRV-DB")
    st_proj_a_pc_1: Computer = network.get_node_by_hostname("ST-PROJ-A-PRV-PC-1")
    st_proj_b_pc_1: Computer = network.get_node_by_hostname("ST-PROJ-B-PRV-PC-1")
    st_proj_c_pc_1: Computer = network.get_node_by_hostname("ST-PROJ-C-PRV-PC-1")

    def ping_network_wide(host):
        assert host.ping(home_office_pc_1.network_interface[1].ip_address)
        assert host.ping(isp_pub_srv_dns.network_interface[1].ip_address)
        assert host.ping(remote_office_pc_1.network_interface[1].ip_address)
        assert host.ping(st_head_office_pc_1.network_interface[1].ip_address)
        assert host.ping(st_human_resources_pc_1.network_interface[1].ip_address)
        assert host.ping(st_data_storage_server.network_interface[1].ip_address)
        assert host.ping(st_data_database_server.network_interface[1].ip_address)
        assert host.ping(st_proj_a_pc_1.network_interface[1].ip_address)
        assert host.ping(st_proj_b_pc_1.network_interface[1].ip_address)
        assert host.ping(st_proj_c_pc_1.network_interface[1].ip_address)

    ping_network_wide(host=home_office_pc_1)
    ping_network_wide(host=isp_pub_srv_dns)
    ping_network_wide(host=remote_office_pc_1)
    ping_network_wide(host=st_head_office_pc_1)
    ping_network_wide(host=st_human_resources_pc_1)
    ping_network_wide(host=st_data_storage_server)
    ping_network_wide(host=st_data_database_server)
    ping_network_wide(host=st_proj_a_pc_1)
    ping_network_wide(host=st_proj_b_pc_1)
    ping_network_wide(host=st_proj_c_pc_1)
