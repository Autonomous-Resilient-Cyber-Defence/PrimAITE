# Plan for creating integration tests for the actions:
# I need to test that the requests coming out of the actions have the intended effect on the simulation.
# I can do this by creating a simulation, and then running the action on the simulation, and then checking
# the state of the simulation.

# Steps for creating the integration tests:
# 1. Create a fixture which creates a simulation.
# 2. Create a fixture which creates a game, including a simple agent with some actions.
# 3. Get the agent to perform an action of my choosing.
# 4. Check that the simulation has changed in the way that I expect.
# 5. Repeat for all actions.

from typing import Dict, Tuple

import pytest

from primaite.game.agent.actions import ActionManager
from primaite.game.agent.interface import AbstractAgent, ProxyAgent
from primaite.game.agent.observations import ICSObservation, ObservationManager
from primaite.game.agent.rewards import RewardFunction
from primaite.game.game import PrimaiteGame
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.computer import Computer
from primaite.simulator.network.hardware.nodes.router import ACLAction, Router
from primaite.simulator.network.hardware.nodes.server import Server
from primaite.simulator.network.hardware.nodes.switch import Switch
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.sim_container import Simulation
from primaite.simulator.system.applications.web_browser import WebBrowser
from primaite.simulator.system.services.dns.dns_client import DNSClient
from primaite.simulator.system.services.dns.dns_server import DNSServer
from primaite.simulator.system.services.web_server.web_server import WebServer
from primaite.simulator.system.software import SoftwareHealthState


class ControlledAgent(AbstractAgent):
    """Agent that can be controlled by the tests."""

    def __init__(
        self,
        agent_name: str,
        action_space: ActionManager,
        observation_space: ObservationManager,
        reward_function: RewardFunction,
    ) -> None:
        super().__init__(
            agent_name=agent_name,
            action_space=action_space,
            observation_space=observation_space,
            reward_function=reward_function,
        )
        self.most_recent_action: Tuple[str, Dict]

    def get_action(self, obs: None, reward: float = 0.0) -> Tuple[str, Dict]:
        """Return the agent's most recent action, formatted in CAOS format."""
        return self.most_recent_action

    def store_action(self, action: Tuple[str, Dict]):
        """Store the most recent action."""
        self.most_recent_action = action


def install_stuff_to_sim(sim: Simulation):
    """Create a simulation with a three computers, two switches, and a router."""

    # 0: Pull out the network
    network = sim.network

    # 1: Set up network hardware
    # 1.1: Configure the router
    router = Router(hostname="router", num_ports=3)
    router.power_on()
    router.configure_port(port=1, ip_address="10.0.1.1", subnet_mask="255.255.255.0")
    router.configure_port(port=2, ip_address="10.0.2.1", subnet_mask="255.255.255.0")

    # 1.2: Create and connect switches
    switch_1 = Switch(hostname="switch_1", num_ports=6)
    switch_1.power_on()
    network.connect(endpoint_a=router.ethernet_ports[1], endpoint_b=switch_1.switch_ports[6])
    router.enable_port(1)
    switch_2 = Switch(hostname="switch_2", num_ports=6)
    switch_2.power_on()
    network.connect(endpoint_a=router.ethernet_ports[2], endpoint_b=switch_2.switch_ports[6])
    router.enable_port(2)

    # 1.3: Create and connect computer
    client_1 = Computer(
        hostname="client_1",
        ip_address="10.0.1.2",
        subnet_mask="255.255.255.0",
        default_gateway="10.0.1.1",
        operating_state=NodeOperatingState.ON,
    )
    client_1.power_on()
    network.connect(
        endpoint_a=client_1.ethernet_port[1],
        endpoint_b=switch_1.switch_ports[1],
    )

    # 1.4: Create and connect servers
    server_1 = Server(
        hostname="server_1",
        ip_address="10.0.2.2",
        subnet_mask="255.255.255.0",
        default_gateway="10.0.2.1",
        operating_state=NodeOperatingState.ON,
    )
    server_1.power_on()
    network.connect(endpoint_a=server_1.ethernet_port[1], endpoint_b=switch_2.switch_ports[1])

    server_2 = Server(
        hostname="server_2",
        ip_address="10.0.2.3",
        subnet_mask="255.255.255.0",
        default_gateway="10.0.2.1",
        operating_state=NodeOperatingState.ON,
    )
    server_2.power_on()
    network.connect(endpoint_a=server_2.ethernet_port[1], endpoint_b=switch_2.switch_ports[2])

    # 2: Configure base ACL
    router.acl.add_rule(action=ACLAction.PERMIT, src_port=Port.ARP, dst_port=Port.ARP, position=22)
    router.acl.add_rule(action=ACLAction.PERMIT, protocol=IPProtocol.ICMP, position=23)
    router.acl.add_rule(action=ACLAction.PERMIT, src_port=Port.DNS, dst_port=Port.DNS, position=1)
    router.acl.add_rule(action=ACLAction.PERMIT, src_port=Port.HTTP, dst_port=Port.HTTP, position=3)

    # 3: Install server software
    server_1.software_manager.install(DNSServer)
    dns_service: DNSServer = server_1.software_manager.software.get("DNSServer")  # noqa
    dns_service.dns_register("example.com", server_2.ip_address)
    server_2.software_manager.install(WebServer)

    # 4: Check that client came pre-installed with web browser and dns client
    assert isinstance(client_1.software_manager.software.get("WebBrowser"), WebBrowser)
    assert isinstance(client_1.software_manager.software.get("DNSClient"), DNSClient)

    # 5: Assert that the simulation starts off in the state that we expect
    assert len(sim.network.nodes) == 6
    assert len(sim.network.links) == 5
    # 5.1: Assert the router is correctly configured
    r = sim.network.routers[0]
    for i, acl_rule in enumerate(r.acl.acl):
        if i == 1:
            assert acl_rule.src_port == acl_rule.dst_port == Port.DNS
        elif i == 3:
            assert acl_rule.src_port == acl_rule.dst_port == Port.HTTP
        elif i == 22:
            assert acl_rule.src_port == acl_rule.dst_port == Port.ARP
        elif i == 23:
            assert acl_rule.protocol == IPProtocol.ICMP
        elif i == 24:
            ...
        else:
            assert acl_rule is None

    # 5.2: Assert the client is correctly configured
    c: Computer = [node for node in sim.network.nodes.values() if node.hostname == "client_1"][0]
    assert c.software_manager.software.get("WebBrowser") is not None
    assert c.software_manager.software.get("DNSClient") is not None
    assert str(c.ethernet_port[1].ip_address) == "10.0.1.2"

    # 5.3: Assert that server_1 is correctly configured
    s1: Server = [node for node in sim.network.nodes.values() if node.hostname == "server_1"][0]
    assert str(s1.ethernet_port[1].ip_address) == "10.0.2.2"
    assert s1.software_manager.software.get("DNSServer") is not None

    # 5.4: Assert that server_2 is correctly configured
    s2: Server = [node for node in sim.network.nodes.values() if node.hostname == "server_2"][0]
    assert str(s2.ethernet_port[1].ip_address) == "10.0.2.3"
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
        {"type": "DONOTHING"},
        {"type": "NODE_SERVICE_SCAN"},
        {"type": "NODE_SERVICE_STOP"},
        {"type": "NODE_SERVICE_START"},
        {"type": "NODE_SERVICE_PAUSE"},
        {"type": "NODE_SERVICE_RESUME"},
        {"type": "NODE_SERVICE_RESTART"},
        {"type": "NODE_SERVICE_DISABLE"},
        {"type": "NODE_SERVICE_ENABLE"},
        {"type": "NODE_APPLICATION_EXECUTE"},
        {"type": "NODE_FILE_SCAN"},
        {"type": "NODE_FILE_CHECKHASH"},
        {"type": "NODE_FILE_DELETE"},
        {"type": "NODE_FILE_REPAIR"},
        {"type": "NODE_FILE_RESTORE"},
        {"type": "NODE_FILE_CORRUPT"},
        {"type": "NODE_FOLDER_SCAN"},
        {"type": "NODE_FOLDER_CHECKHASH"},
        {"type": "NODE_FOLDER_REPAIR"},
        {"type": "NODE_FOLDER_RESTORE"},
        {"type": "NODE_OS_SCAN"},
        {"type": "NODE_SHUTDOWN"},
        {"type": "NODE_STARTUP"},
        {"type": "NODE_RESET"},
        {"type": "NETWORK_ACL_ADDRULE", "options": {"target_router_hostname": "router"}},
        {"type": "NETWORK_ACL_REMOVERULE", "options": {"target_router_hostname": "router"}},
        {"type": "NETWORK_NIC_ENABLE"},
        {"type": "NETWORK_NIC_DISABLE"},
    ]

    action_space = ActionManager(
        game=game,
        actions=actions,  # ALL POSSIBLE ACTIONS
        nodes=[
            {"node_name": "client_1", "applications": [{"application_name": "WebBrowser"}]},
            {"node_name": "server_1", "services": [{"service_name": "DNSServer"}]},
            {"node_name": "server_2", "services": [{"service_name": "WebServer"}]},
        ],
        max_folders_per_node=2,
        max_files_per_folder=2,
        max_services_per_node=2,
        max_applications_per_node=2,
        max_nics_per_node=2,
        max_acl_rules=10,
        protocols=["TCP", "UDP", "ICMP"],
        ports=["HTTP", "DNS", "ARP"],
        ip_address_list=["10.0.1.1", "10.0.1.2", "10.0.2.1", "10.0.2.2", "10.0.2.3"],
        act_map={},
    )
    observation_space = ObservationManager(ICSObservation())
    reward_function = RewardFunction()

    test_agent = ControlledAgent(
        agent_name="test_agent",
        action_space=action_space,
        observation_space=observation_space,
        reward_function=reward_function,
    )

    game.agents.append(test_agent)

    return (game, test_agent)


# def test_test(game_and_agent:Tuple[PrimaiteGame, ProxyAgent]):
#     game, agent = game_and_agent


def test_do_nothing_integration(game_and_agent: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that the DoNothingAction can form a request and that it is accepted by the simulation."""
    game, agent = game_and_agent

    action = ("DONOTHING", {})
    agent.store_action(action)
    game.step()


@pytest.mark.skip(reason="Waiting to merge ticket 2160")
def test_node_service_scan_integration(game_and_agent: Tuple[PrimaiteGame, ProxyAgent]):
    """
    Test that the NodeServiceScanAction can form a request and that it is accepted by the simulation.

    The health status of applications is not always updated in the state dict, rather the agent needs to perform a scan.
    Therefore, we set the web browser to be corrupted, check the state is still good, then perform a scan, and check
    that the state changes to the true value.
    """
    game, agent = game_and_agent

    browser = game.simulation.network.get_node_by_hostname("client_1").software_manager.software.get("WebBrowser")
    browser.health_state_actual = SoftwareHealthState.COMPROMISED

    state_before = game.get_sim_state()
    assert (
        game.get_sim_state()["network"]["nodes"]["client_1"]["applications"]["WebBrowser"]["health_state"]
        == SoftwareHealthState.GOOD
    )
    action = ("NODE_SERVICE_SCAN", {"node_id": 0, "service_id": 0})
    agent.store_action(action)
    game.step()
    state_after = game.get_sim_state()
    pass
    assert (
        game.get_sim_state()["network"]["nodes"]["client_1"]["services"]["WebBrowser"]["health_state"]
        == SoftwareHealthState.COMPROMISED
    )
