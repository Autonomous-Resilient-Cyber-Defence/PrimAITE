# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from typing import Any, Dict, Optional, Tuple

import pytest
import yaml
from pydantic import Field
from ray import init as rayinit

from primaite import getLogger, PRIMAITE_PATHS
from primaite.game.agent.actions import ActionManager
from primaite.game.agent.interface import AbstractAgent
from primaite.game.agent.observations.observation_manager import NestedObservation, ObservationManager
from primaite.game.agent.rewards import RewardFunction
from primaite.game.agent.scripted_agents.probabilistic_agent import ProbabilisticAgent
from primaite.game.game import PrimaiteGame
from primaite.simulator.file_system.file_system import FileSystem
from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.hardware.nodes.network.router import ACLAction, Router
from primaite.simulator.network.hardware.nodes.network.switch import Switch
from primaite.simulator.network.networks import arcd_uc2_network
from primaite.simulator.sim_container import Simulation
from primaite.simulator.system.applications.application import Application
from primaite.simulator.system.applications.web_browser import WebBrowser
from primaite.simulator.system.core.sys_log import SysLog
from primaite.simulator.system.services.dns.dns_client import DNSClient
from primaite.simulator.system.services.dns.dns_server import DNSServer
from primaite.simulator.system.services.service import Service
from primaite.simulator.system.services.web_server.web_server import WebServer
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.port import PORT_LOOKUP
from tests import TEST_ASSETS_ROOT

rayinit()
ACTION_SPACE_NODE_VALUES = 1
ACTION_SPACE_NODE_ACTION_VALUES = 1

_LOGGER = getLogger(__name__)


class DummyService(Service):
    """Test Service class"""

    def describe_state(self) -> Dict:
        return super().describe_state()

    def __init__(self, **kwargs):
        kwargs["name"] = "DummyService"
        kwargs["port"] = PORT_LOOKUP["HTTP"]
        kwargs["protocol"] = PROTOCOL_LOOKUP["TCP"]
        super().__init__(**kwargs)

    def receive(self, payload: Any, session_id: str, **kwargs) -> bool:
        pass


class DummyApplication(Application, identifier="DummyApplication"):
    """Test Application class"""

    def __init__(self, **kwargs):
        kwargs["name"] = "DummyApplication"
        kwargs["port"] = PORT_LOOKUP["HTTP"]
        kwargs["protocol"] = PROTOCOL_LOOKUP["TCP"]
        super().__init__(**kwargs)

    def describe_state(self) -> Dict:
        return super().describe_state()


@pytest.fixture(scope="function")
def uc2_network() -> Network:
    with open(PRIMAITE_PATHS.user_config_path / "example_config" / "data_manipulation.yaml") as f:
        cfg = yaml.safe_load(f)
    game = PrimaiteGame.from_config(cfg)
    return game.simulation.network


@pytest.fixture(scope="function")
def service(file_system) -> DummyService:
    return DummyService(
        name="DummyService", port=PORT_LOOKUP["ARP"], file_system=file_system, sys_log=SysLog(hostname="dummy_service")
    )


@pytest.fixture(scope="function")
def service_class():
    return DummyService


@pytest.fixture(scope="function")
def application(file_system) -> DummyApplication:
    return DummyApplication(
        name="DummyApplication",
        port=PORT_LOOKUP["ARP"],
        file_system=file_system,
        sys_log=SysLog(hostname="dummy_application"),
    )


@pytest.fixture(scope="function")
def application_class():
    return DummyApplication


@pytest.fixture(scope="function")
def file_system() -> FileSystem:
    computer = Computer(hostname="fs_node", ip_address="192.168.1.2", subnet_mask="255.255.255.0", start_up_duration=0)
    computer.power_on()
    return computer.file_system


@pytest.fixture(scope="function")
def client_server() -> Tuple[Computer, Server]:
    network = Network()

    # Create Computer
    computer = Computer(
        hostname="computer",
        ip_address="192.168.1.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    computer.power_on()

    # Create Server
    server = Server(
        hostname="server",
        ip_address="192.168.1.3",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    server.power_on()

    # Connect Computer and Server
    network.connect(computer.network_interface[1], server.network_interface[1])

    # Should be linked
    assert next(iter(network.links.values())).is_up

    return computer, server


@pytest.fixture(scope="function")
def client_switch_server() -> Tuple[Computer, Switch, Server]:
    network = Network()

    # Create Computer
    computer = Computer(
        hostname="computer",
        ip_address="192.168.1.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    computer.power_on()

    # Create Server
    server = Server(
        hostname="server",
        ip_address="192.168.1.3",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    server.power_on()

    switch = Switch(hostname="switch", start_up_duration=0)
    switch.power_on()

    network.connect(endpoint_a=computer.network_interface[1], endpoint_b=switch.network_interface[1])
    network.connect(endpoint_a=server.network_interface[1], endpoint_b=switch.network_interface[2])

    assert all(link.is_up for link in network.links.values())

    return computer, switch, server


@pytest.fixture(scope="function")
def example_network() -> Network:
    """
    Create the network used for testing.

    Should only contain the nodes and links.
    This would act as the base network and services and applications are installed in the relevant test file,

    --------------                                                                          --------------
    |  client_1  |-----                                                                 ----|  server_1  |
    --------------    |     --------------      --------------      --------------     |    --------------
                      ------|  switch_2  |------|  router_1  |------|  switch_1  |------
    --------------    |     --------------      --------------      --------------     |   --------------
    |  client_2  |----                                                                 ----|  server_2  |
    --------------                                                                         --------------
    """
    network = Network()

    # Router 1
    router_1 = Router(hostname="router_1", start_up_duration=0)
    router_1.power_on()
    router_1.configure_port(port=1, ip_address="192.168.1.1", subnet_mask="255.255.255.0")
    router_1.configure_port(port=2, ip_address="192.168.10.1", subnet_mask="255.255.255.0")

    # Switch 1
    switch_1 = Switch(hostname="switch_1", num_ports=8, start_up_duration=0)
    switch_1.power_on()

    network.connect(endpoint_a=router_1.network_interface[1], endpoint_b=switch_1.network_interface[8])
    router_1.enable_port(1)

    # Switch 2
    switch_2 = Switch(hostname="switch_2", num_ports=8, start_up_duration=0)
    switch_2.power_on()
    network.connect(endpoint_a=router_1.network_interface[2], endpoint_b=switch_2.network_interface[8])
    router_1.enable_port(2)

    # Client 1
    client_1 = Computer(
        hostname="client_1",
        ip_address="192.168.10.21",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.10.1",
        start_up_duration=0,
    )
    client_1.power_on()
    network.connect(endpoint_b=client_1.network_interface[1], endpoint_a=switch_2.network_interface[1])

    # Client 2
    client_2 = Computer(
        hostname="client_2",
        ip_address="192.168.10.22",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.10.1",
        start_up_duration=0,
    )
    client_2.power_on()
    network.connect(endpoint_b=client_2.network_interface[1], endpoint_a=switch_2.network_interface[2])

    # Server 1
    server_1 = Server(
        hostname="server_1",
        ip_address="192.168.1.10",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    server_1.power_on()
    network.connect(endpoint_b=server_1.network_interface[1], endpoint_a=switch_1.network_interface[1])

    # DServer 2
    server_2 = Server(
        hostname="server_2",
        ip_address="192.168.1.14",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    server_2.power_on()
    network.connect(endpoint_b=server_2.network_interface[1], endpoint_a=switch_1.network_interface[2])

    router_1.acl.add_rule(action=ACLAction.PERMIT, position=1)

    assert all(link.is_up for link in network.links.values())

    return network


class ControlledAgent(AbstractAgent, identifier="ControlledAgent"):
    """Agent that can be controlled by the tests."""

    config: "ControlledAgent.ConfigSchema" = Field(default_factory=lambda: ControlledAgent.ConfigSchema())
    most_recent_action: Optional[Tuple[str, Dict]] = None

    class ConfigSchema(AbstractAgent.ConfigSchema):
        """Configuration Schema for Abstract Agent used in tests."""

        type: str = "ControlledAgent"

    def get_action(self, obs: None, timestep: int = 0) -> Tuple[str, Dict]:
        """Return the agent's most recent action, formatted in CAOS format."""
        return self.most_recent_action

    def store_action(self, action: Tuple[str, Dict]):
        """Store the most recent action."""
        self.most_recent_action = action


def install_stuff_to_sim(sim: Simulation):
    """Create a simulation with a computer, two servers, two switches, and a router."""

    # 0: Pull out the network
    network = sim.network

    # 1: Set up network hardware
    # 1.1: Configure the router
    router = Router(hostname="router", num_ports=3, start_up_duration=0)
    router.power_on()
    router.configure_port(port=1, ip_address="10.0.1.1", subnet_mask="255.255.255.0")
    router.configure_port(port=2, ip_address="10.0.2.1", subnet_mask="255.255.255.0")

    # 1.2: Create and connect switches
    switch_1 = Switch(hostname="switch_1", num_ports=6, start_up_duration=0)
    switch_1.power_on()
    network.connect(endpoint_a=router.network_interface[1], endpoint_b=switch_1.network_interface[6])
    router.enable_port(1)
    switch_2 = Switch(hostname="switch_2", num_ports=6, start_up_duration=0)
    switch_2.power_on()
    network.connect(endpoint_a=router.network_interface[2], endpoint_b=switch_2.network_interface[6])
    router.enable_port(2)

    # 1.3: Create and connect computer
    client_1 = Computer(
        hostname="client_1",
        ip_address="10.0.1.2",
        subnet_mask="255.255.255.0",
        default_gateway="10.0.1.1",
        start_up_duration=0,
    )
    client_1.power_on()
    network.connect(
        endpoint_a=client_1.network_interface[1],
        endpoint_b=switch_1.network_interface[1],
    )

    # 1.4: Create and connect servers
    server_1 = Server(
        hostname="server_1",
        ip_address="10.0.2.2",
        subnet_mask="255.255.255.0",
        default_gateway="10.0.2.1",
        start_up_duration=0,
    )
    server_1.power_on()
    network.connect(endpoint_a=server_1.network_interface[1], endpoint_b=switch_2.network_interface[1])

    server_2 = Server(
        hostname="server_2",
        ip_address="10.0.2.3",
        subnet_mask="255.255.255.0",
        default_gateway="10.0.2.1",
        start_up_duration=0,
    )
    server_2.power_on()
    network.connect(endpoint_a=server_2.network_interface[1], endpoint_b=switch_2.network_interface[2])

    # 2: Configure base ACL
    router.acl.add_rule(action=ACLAction.PERMIT, src_port=PORT_LOOKUP["ARP"], dst_port=PORT_LOOKUP["ARP"], position=22)
    router.acl.add_rule(action=ACLAction.PERMIT, protocol=PROTOCOL_LOOKUP["ICMP"], position=23)
    router.acl.add_rule(action=ACLAction.PERMIT, src_port=PORT_LOOKUP["DNS"], dst_port=PORT_LOOKUP["DNS"], position=1)
    router.acl.add_rule(action=ACLAction.PERMIT, src_port=PORT_LOOKUP["HTTP"], dst_port=PORT_LOOKUP["HTTP"], position=3)

    # 3: Install server software
    server_1.software_manager.install(DNSServer)
    dns_service: DNSServer = server_1.software_manager.software.get("DNSServer")  # noqa
    dns_service.dns_register("www.example.com", server_2.network_interface[1].ip_address)
    server_2.software_manager.install(WebServer)

    # 3.1: Ensure that the dns clients are configured correctly
    client_1.software_manager.software.get("DNSClient").dns_server = server_1.network_interface[1].ip_address
    server_2.software_manager.software.get("DNSClient").dns_server = server_1.network_interface[1].ip_address

    # 4: Check that client came pre-installed with web browser and dns client
    assert isinstance(client_1.software_manager.software.get("WebBrowser"), WebBrowser)
    assert isinstance(client_1.software_manager.software.get("DNSClient"), DNSClient)

    # 4.1: Create a file on the computer
    client_1.file_system.create_file("cat.png", 300, folder_name="downloads")

    # 5: Assert that the simulation starts off in the state that we expect
    assert len(sim.network.nodes) == 6
    assert len(sim.network.links) == 5

    # 5.1: Assert the router is correctly configured
    r = sim.network.router_nodes[0]
    for i, acl_rule in enumerate(r.acl.acl):
        if i == 1:
            assert acl_rule.src_port == acl_rule.dst_port == PORT_LOOKUP["DNS"]
        elif i == 3:
            assert acl_rule.src_port == acl_rule.dst_port == PORT_LOOKUP["HTTP"]
        elif i == 22:
            assert acl_rule.src_port == acl_rule.dst_port == PORT_LOOKUP["ARP"]
        elif i == 23:
            assert acl_rule.protocol == PROTOCOL_LOOKUP["ICMP"]
        elif i == 24:
            ...
        else:
            assert acl_rule is None

    # 5.2: Assert the client is correctly configured
    c: Computer = [node for node in sim.network.nodes.values() if node.hostname == "client_1"][0]
    assert c.software_manager.software.get("WebBrowser") is not None
    assert c.software_manager.software.get("DNSClient") is not None
    assert str(c.network_interface[1].ip_address) == "10.0.1.2"

    # 5.3: Assert that server_1 is correctly configured
    s1: Server = [node for node in sim.network.nodes.values() if node.hostname == "server_1"][0]
    assert str(s1.network_interface[1].ip_address) == "10.0.2.2"
    assert s1.software_manager.software.get("DNSServer") is not None

    # 5.4: Assert that server_2 is correctly configured
    s2: Server = [node for node in sim.network.nodes.values() if node.hostname == "server_2"][0]
    assert str(s2.network_interface[1].ip_address) == "10.0.2.3"
    assert s2.software_manager.software.get("WebServer") is not None

    # 6: Return the simulation
    return sim


@pytest.fixture
def game_and_agent():
    """Create a game with a simple agent that can be controlled by the tests."""
    game = PrimaiteGame()
    sim = game.simulation
    install_stuff_to_sim(sim)

    actions = [
        {"type": "do_nothing"},
        {"type": "node_service_scan"},
        {"type": "node_service_stop"},
        {"type": "node_service_start"},
        {"type": "node_service_pause"},
        {"type": "node_service_resume"},
        {"type": "node_service_restart"},
        {"type": "node_service_disable"},
        {"type": "node_service_enable"},
        {"type": "node_service_fix"},
        {"type": "node_application_execute"},
        {"type": "node_application_scan"},
        {"type": "node_application_close"},
        {"type": "node_application_fix"},
        {"type": "node_application_install"},
        {"type": "node_application_remove"},
        {"type": "node_file_create"},
        {"type": "node_file_scan"},
        {"type": "node_file_checkhash"},
        {"type": "node_file_delete"},
        {"type": "node_file_repair"},
        {"type": "node_file_restore"},
        {"type": "node_file_corrupt"},
        {"type": "node_file_access"},
        {"type": "node_folder_create"},
        {"type": "node_folder_scan"},
        {"type": "node_folder_checkhash"},
        {"type": "node_folder_repair"},
        {"type": "node_folder_restore"},
        {"type": "node_os_scan"},
        {"type": "node_shutdown"},
        {"type": "node_startup"},
        {"type": "node_reset"},
        {"type": "router_acl_add_rule"},
        {"type": "router_acl_remove_rule"},
        {"type": "host_nic_enable"},
        {"type": "host_nic_disable"},
        {"type": "network_port_enable"},
        {"type": "network_port_disable"},
        {"type": "configure_c2_beacon"},
        {"type": "c2_server_ransomware_launch"},
        {"type": "c2_server_ransomware_configure"},
        {"type": "c2_server_terminal_command"},
        {"type": "c2_server_data_exfiltrate"},
        {"type": "node_account_change_password"},
        {"type": "node_session_remote_login"},
        {"type": "node_session_remote_logoff"},
        {"type": "node_send_remote_command"},
    ]

    action_space = ActionManager(
        actions=actions,  # ALL POSSIBLE ACTIONS
        act_map={},
    )
    observation_space = ObservationManager(NestedObservation(components={}))
    reward_function = RewardFunction()

    config = {
        "type": "ControlledAgent",
        "agent_name": "test_agent",
        "action_manager": action_space,
        "observation_manager": observation_space,
        "reward_function": reward_function,
        "agent_settings": {},
    }

    test_agent = ControlledAgent.from_config(config=config)

    game.agents["test_agent"] = test_agent

    game.setup_reward_sharing()

    return (game, test_agent)
