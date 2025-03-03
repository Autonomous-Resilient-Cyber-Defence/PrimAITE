# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

import pytest
import yaml

from primaite.config.load import _EXAMPLE_CFG, load
from primaite.game.game import PrimaiteGame
from primaite.session.environment import PrimaiteGymEnv
from primaite.simulator.file_system.file import File
from primaite.simulator.file_system.file_system_item_abc import FileSystemItemHealthStatus
from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.hardware.nodes.network.firewall import Firewall
from primaite.simulator.system.applications.application import ApplicationOperatingState
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.applications.red_applications.c2.c2_beacon import C2Beacon
from primaite.simulator.system.applications.red_applications.ransomware_script import RansomwareScript
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
ATTACK_AGENT_INDEX = 32


@pytest.fixture(scope="function")
def uc7_environment() -> PrimaiteGymEnv:
    with open(_EXAMPLE_CFG / "uc7_config.yaml", mode="r") as uc7_config:
        cfg = yaml.safe_load(uc7_config)
    env = PrimaiteGymEnv(env_config=cfg)
    return env


def assert_agent_reward(env: PrimaiteGymEnv, agent_name: str, positive: bool):
    """Asserts that a given agent has a reward that is below/above or equal to 0 dependant on arguments."""
    agent_reward = env.game.agents[agent_name].reward_function.total_reward
    if agent_name == "defender":
        return  # ignore blue agent
    if positive is True:
        assert agent_reward >= 0  # Asserts that no agents are below a total reward of 0
    elif positive is False:
        assert agent_reward <= 0  # Asserts that no agents are above a total reward of 0


def test_green_agent_positive_reward(uc7_environment):
    """Confirms that the UC7 Green Agents receive a positive reward (Default Behaviour)."""
    env: PrimaiteGymEnv = uc7_environment

    # Performing no changes to the environment. Default Behaviour

    # Stepping 60 times in the environment
    for _ in range(60):
        env.step(0)

    for agent in env.game.agents:
        assert_agent_reward(env=env, agent_name=env.game.agents[agent].config.ref, positive=True)


def test_green_agent_negative_reward(uc7_environment):
    """Confirms that the UC7 Green Agents receive a negative reward. (Disabled web-server and database-service)"""

    env: PrimaiteGymEnv = uc7_environment

    # Purposefully disabling the following services:

    # 1. Disabling the web-server
    st_dmz_pub_srv_web: Server = env.game.simulation.network.get_node_by_hostname("ST_DMZ-PUB-SRV-WEB")
    st_web_server = st_dmz_pub_srv_web.software_manager.software["web-server"]
    st_web_server.operating_state = ServiceOperatingState.DISABLED
    assert st_web_server.operating_state == ServiceOperatingState.DISABLED

    # 2. Disabling the DatabaseServer
    st_data_database_server: Server = env.game.simulation.network.get_node_by_hostname("ST_DATA-PRV-SRV-DB")
    database_service: DatabaseService = st_data_database_server.software_manager.software["database-service"]
    database_service.operating_state = ServiceOperatingState.DISABLED
    assert database_service.operating_state == ServiceOperatingState.DISABLED

    # Stepping 100 times in the environment
    for _ in range(100):
        env.step(0)

    for agent in env.game.agents:
        assert_agent_reward(env=env, agent_name=env.game.agents[agent].config.ref, positive=False)


def test_tap001_default_behaviour(uc7_environment):
    """Confirms that the TAP001 expected simulation impacts works as expected in the UC7 environment."""
    env: PrimaiteGymEnv = uc7_environment
    env.reset()
    network = env.game.simulation.network

    # Running for 128 episodes
    for _ in range(128):
        env.step(0)

    some_tech_proj_a_pc_1: Computer = network.get_node_by_hostname("ST_PROJ-A-PRV-PC-1")

    # Asserting that the `malware_dropper.ps1` was created.

    malware_dropper_file: File = some_tech_proj_a_pc_1.file_system.get_file("downloads", "malware_dropper.ps1")
    assert malware_dropper_file.health_status == FileSystemItemHealthStatus.GOOD

    # Asserting that the `RansomwareScript` launched successfully.

    ransomware_script: RansomwareScript = some_tech_proj_a_pc_1.software_manager.software["ransomware-script"]
    assert ransomware_script.health_state_actual == SoftwareHealthState.GOOD
    assert ransomware_script.operating_state == ApplicationOperatingState.RUNNING

    # Asserting that the `C2Beacon` connected to the `C2Server`.

    c2_beacon: C2Beacon = some_tech_proj_a_pc_1.software_manager.software["c2-beacon"]
    assert c2_beacon.health_state_actual == SoftwareHealthState.GOOD
    assert c2_beacon.operating_state == ApplicationOperatingState.RUNNING
    assert c2_beacon.c2_connection_active == True

    # Asserting that the target database was successfully corrupted.
    some_tech_data_server_database: Server = network.get_node_by_hostname("ST_DATA-PRV-SRV-DB")
    database_file: File = some_tech_data_server_database.file_system.get_file(
        folder_name="database", file_name="database.db"
    )
    assert database_file.health_status == FileSystemItemHealthStatus.CORRUPT


def test_tap003_default_behaviour(uc7_environment):
    """Confirms that the TAP003 expected simulation impacts works as expected in the UC7 environment."""
    from primaite.simulator.network.hardware.nodes.network.router import ACLAction, Router
    from primaite.simulator.network.transmission.network_layer import IPPacket, IPProtocol
    from primaite.utils.validation.port import PORT_LOOKUP

    def uc7_environment_tap003() -> PrimaiteGymEnv:
        with open(_EXAMPLE_CFG / "uc7_config_tap003.yaml", mode="r") as uc7_config:
            cfg = yaml.safe_load(uc7_config)
            cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["starting_nodes"] = ["ST_PROJ-A-PRV-PC-1"]
            cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["default_starting_node"] = "ST_PROJ-A-PRV-PC-1"
        env = PrimaiteGymEnv(env_config=cfg)
        return env

    env: PrimaiteGymEnv = uc7_environment_tap003()
    env.reset()
    # Running for 128 episodes
    for _ in range(128):
        env.step(0)
    network = env.game.simulation.network

    # Asserting that a malicious ACL has been added to ST_INTRA-PRV-RT-DR-1
    st_intra_prv_rt_dr_1: Router = network.get_node_by_hostname(hostname="ST_INTRA-PRV-RT-DR-1")
    assert st_intra_prv_rt_dr_1.acl.acl[1].action == ACLAction.DENY
    assert st_intra_prv_rt_dr_1.acl.acl[1].protocol == "tcp"
    assert st_intra_prv_rt_dr_1.acl.acl[1].src_port == PORT_LOOKUP.get("POSTGRES_SERVER")
    assert st_intra_prv_rt_dr_1.acl.acl[1].dst_port == PORT_LOOKUP.get("POSTGRES_SERVER")

    # Asserting that a malicious ACL has been added to ST_INTRA-PRV-RT-CR
    st_intra_prv_rt_cr: Router = network.get_node_by_hostname(hostname="ST_INTRA-PRV-RT-CR")
    assert st_intra_prv_rt_cr.acl.acl[1].action == ACLAction.DENY
    assert st_intra_prv_rt_cr.acl.acl[1].protocol == "tcp"
    assert st_intra_prv_rt_cr.acl.acl[1].src_port == PORT_LOOKUP.get("HTTP")
    assert st_intra_prv_rt_cr.acl.acl[1].dst_port == PORT_LOOKUP.get("HTTP")

    # Asserting that a malicious ACL has been added to REM-PUB-RT-DR
    rem_pub_rt_dr: Router = network.get_node_by_hostname(hostname="REM-PUB-RT-DR")
    assert rem_pub_rt_dr.acl.acl[1].action == ACLAction.DENY
    assert rem_pub_rt_dr.acl.acl[1].protocol == "tcp"
    assert rem_pub_rt_dr.acl.acl[1].src_port == PORT_LOOKUP.get("DNS")
    assert rem_pub_rt_dr.acl.acl[1].dst_port == PORT_LOOKUP.get("DNS")
