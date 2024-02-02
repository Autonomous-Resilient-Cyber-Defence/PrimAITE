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
from primaite.simulator.file_system.file_system_item_abc import FileSystemItemHealthStatus
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
    """Create a simulation with a computer, two servers, two switches, and a router."""

    # 0: Pull out the network
    network = sim.network

    # 1: Set up network hardware
    # 1.1: Configure the router
    router = Router(hostname="router", num_ports=3, operating_state=NodeOperatingState.ON)
    router.power_on()
    router.configure_port(port=1, ip_address="10.0.1.1", subnet_mask="255.255.255.0")
    router.configure_port(port=2, ip_address="10.0.2.1", subnet_mask="255.255.255.0")

    # 1.2: Create and connect switches
    switch_1 = Switch(hostname="switch_1", num_ports=6, operating_state=NodeOperatingState.ON)
    switch_1.power_on()
    network.connect(endpoint_a=router.ethernet_ports[1], endpoint_b=switch_1.switch_ports[6])
    router.enable_port(1)
    switch_2 = Switch(hostname="switch_2", num_ports=6, operating_state=NodeOperatingState.ON)
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
    dns_service.dns_register("www.example.com", server_2.ip_address)
    server_2.software_manager.install(WebServer)

    # 3.1: Ensure that the dns clients are configured correctly
    client_1.software_manager.software.get("DNSClient").dns_server = server_1.ethernet_port[1].ip_address
    server_2.software_manager.software.get("DNSClient").dns_server = server_1.ethernet_port[1].ip_address

    # 4: Check that client came pre-installed with web browser and dns client
    assert isinstance(client_1.software_manager.software.get("WebBrowser"), WebBrowser)
    assert isinstance(client_1.software_manager.software.get("DNSClient"), DNSClient)

    # 4.1: Create a file on the computer
    client_1.file_system.create_file("cat.png", 300, folder_name="downloads")

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
        {"type": "NODE_SERVICE_PATCH"},
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
            {
                "node_name": "client_1",
                "applications": [{"application_name": "WebBrowser"}],
                "folders": [{"folder_name": "downloads", "files": [{"file_name": "cat.png"}]}],
            },
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


@pytest.mark.skip(reason="Waiting to merge ticket 2166")
def test_node_service_scan_integration(game_and_agent: Tuple[PrimaiteGame, ProxyAgent]):
    """
    Test that the NodeServiceScanAction can form a request and that it is accepted by the simulation.

    The health status of applications is not always updated in the state dict, rather the agent needs to perform a scan.
    Therefore, we set a service to be compromised, check the state is still good, then perform a scan, and check
    that the state changes to the true value.
    """
    game, agent = game_and_agent

    # 1: Check that the service starts off in a good state, and that visible state is hidden until first scan
    svc = game.simulation.network.get_node_by_hostname("client_1").software_manager.software.get("DNSClient")
    assert svc.health_state_actual == SoftwareHealthState.GOOD
    assert svc.health_state_visible == SoftwareHealthState.UNUSED

    # 2: Scan and check that the visible state is now correct
    action = ("NODE_SERVICE_SCAN", {"node_id": 0, "service_id": 0})
    agent.store_action(action)
    game.step()
    assert svc.health_state_actual == SoftwareHealthState.GOOD
    assert svc.health_state_visible == SoftwareHealthState.GOOD

    # 3: Corrupt the service and check that the visible state is still good
    svc.health_state_actual = SoftwareHealthState.COMPROMISED
    assert svc.health_state_visible == SoftwareHealthState.GOOD

    # 4: Scan and check that the visible state is now correct
    action = ("NODE_SERVICE_SCAN", {"node_id": 0, "service_id": 0})
    agent.store_action(action)
    game.step()
    assert svc.health_state_actual == SoftwareHealthState.COMPROMISED
    assert svc.health_state_visible == SoftwareHealthState.COMPROMISED


def test_node_service_patch_integration(game_and_agent: Tuple[PrimaiteGame, ProxyAgent]):
    """
    Test that the NodeServicePatchAction can form a request and that it is accepted by the simulation.

    When you initiate a patch action, the software health state turns to PATCHING, then after a few steps, it goes
    to GOOD.
    """
    game, agent = game_and_agent

    # 1: Corrupt the service
    svc = game.simulation.network.get_node_by_hostname("server_1").software_manager.software.get("DNSServer")
    svc.health_state_actual = SoftwareHealthState.COMPROMISED

    # 2: Apply a patch action
    action = ("NODE_SERVICE_PATCH", {"node_id": 1, "service_id": 0})
    agent.store_action(action)
    game.step()

    # 3: Check that the service is now in the patching state
    assert svc.health_state_actual == SoftwareHealthState.PATCHING

    # 4: perform a few do-nothing steps and check that the service is now in the good state
    action = ("DONOTHING", {})
    agent.store_action(action)
    game.step()
    assert svc.health_state_actual == SoftwareHealthState.GOOD


def test_network_acl_addrule_integration(game_and_agent: Tuple[PrimaiteGame, ProxyAgent]):
    """
    Test that the NetworkACLAddRuleAction can form a request and that it is accepted by the simulation.

    The ACL starts off with 4 rules, and we add a rule, and check that the ACL now has 5 rules.
    """
    game, agent = game_and_agent

    # 1: Check that traffic is normal and acl starts off with 4 rules.
    client_1 = game.simulation.network.get_node_by_hostname("client_1")
    server_1 = game.simulation.network.get_node_by_hostname("server_1")
    server_2 = game.simulation.network.get_node_by_hostname("server_2")
    router = game.simulation.network.get_node_by_hostname("router")
    assert router.acl.num_rules == 4
    assert client_1.ping("10.0.2.3")  # client_1 can ping server_2
    assert server_2.ping("10.0.1.2")  # server_2 can ping client_1

    # 2: Add a rule to block client 1 from reaching server 2 on router
    action = (
        "NETWORK_ACL_ADDRULE",
        {
            "position": 4,  # 4th rule
            "permission": 2,  # DENY
            "source_ip_id": 3,  # 10.0.1.2 (client_1)
            "dest_ip_id": 6,  # 10.0.2.3 (server_2)
            "dest_port_id": 1,  # ALL
            "source_port_id": 1,  # ALL
            "protocol_id": 1,  # ALL
        },
    )
    agent.store_action(action)
    game.step()

    # 3: Check that the ACL now has 5 rules, and that client 1 cannot ping server 2
    assert router.acl.num_rules == 5
    assert not client_1.ping("10.0.2.3")  # Cannot ping server_2
    assert client_1.ping("10.0.2.2")  # Can ping server_1
    assert not server_2.ping(
        "10.0.1.2"
    )  # Server 2 can't ping client_1 (although rule is one-way, the ping response is blocked)

    # 4: Add a rule to block server_1 from reaching server_2 on router (this should not affect comms as they are on same subnet)
    action = (
        "NETWORK_ACL_ADDRULE",
        {
            "position": 5,  # 5th rule
            "permission": 2,  # DENY
            "source_ip_id": 5,  # 10.0.2.2 (server_1)
            "dest_ip_id": 6,  # 10.0.2.3 (server_2)
            "dest_port_id": 1,  # ALL
            "source_port_id": 1,  # ALL
            "protocol_id": 1,  # ALL
        },
    )
    agent.store_action(action)
    game.step()

    # 5: Check that the ACL now has 6 rules, but that server_1 can still ping server_2
    assert router.acl.num_rules == 6
    assert server_1.ping("10.0.2.3")  # Can ping server_2


def test_network_acl_removerule_integration(game_and_agent: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that the NetworkACLRemoveRuleAction can form a request and that it is accepted by the simulation."""
    game, agent = game_and_agent

    # 1: Check that http traffic is going across the network nicely.
    client_1 = game.simulation.network.get_node_by_hostname("client_1")
    server_1 = game.simulation.network.get_node_by_hostname("server_1")
    router = game.simulation.network.get_node_by_hostname("router")

    browser: WebBrowser = client_1.software_manager.software.get("WebBrowser")
    browser.run()
    browser.target_url = "http://www.example.com"
    assert browser.get_webpage()  # check that the browser can access example.com before we block it

    # 2: Remove rule that allows HTTP traffic across the network
    action = (
        "NETWORK_ACL_REMOVERULE",
        {
            "position": 3,  # 4th rule
        },
    )
    agent.store_action(action)
    game.step()

    # 3: Check that the ACL now has 3 rules, and that client 1 cannot access example.com
    assert router.acl.num_rules == 3
    assert not browser.get_webpage()
    client_1.software_manager.software.get("DNSClient").dns_cache.clear()
    assert client_1.ping("10.0.2.2")  # pinging still works because ICMP is allowed
    assert client_1.ping("10.0.2.3")


def test_network_nic_disable_integration(game_and_agent: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that the NetworkNICDisableAction can form a request and that it is accepted by the simulation."""
    game, agent = game_and_agent

    # 1: Check that client_1 can access the network
    client_1 = game.simulation.network.get_node_by_hostname("client_1")
    server_1 = game.simulation.network.get_node_by_hostname("server_1")
    server_2 = game.simulation.network.get_node_by_hostname("server_2")

    browser: WebBrowser = client_1.software_manager.software.get("WebBrowser")
    browser.run()
    browser.target_url = "http://www.example.com"
    assert browser.get_webpage()  # check that the browser can access example.com before we block it

    # 2: Disable the NIC on client_1
    action = (
        "NETWORK_NIC_DISABLE",
        {
            "node_id": 0,  # client_1
            "nic_id": 0,  # the only nic (eth-1)
        },
    )
    agent.store_action(action)
    game.step()

    # 3: Check that the NIC is disabled, and that client 1 cannot access example.com
    assert client_1.ethernet_port[1].enabled == False
    assert not browser.get_webpage()
    assert not client_1.ping("10.0.2.2")
    assert not client_1.ping("10.0.2.3")

    # 4: check that servers can still communicate
    assert server_1.ping("10.0.2.3")


def test_network_nic_enable_integration(game_and_agent: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that the NetworkNICEnableAction can form a request and that it is accepted by the simulation."""

    game, agent = game_and_agent

    # 1: Disable client_1 nic
    client_1 = game.simulation.network.get_node_by_hostname("client_1")
    client_1.ethernet_port[1].disable()
    assert not client_1.ping("10.0.2.2")

    # 2: Use action to enable nic
    action = (
        "NETWORK_NIC_ENABLE",
        {
            "node_id": 0,  # client_1
            "nic_id": 0,  # the only nic (eth-1)
        },
    )
    agent.store_action(action)
    game.step()

    # 3: Check that the NIC is enabled, and that client 1 can ping again
    assert client_1.ethernet_port[1].enabled == True
    assert client_1.ping("10.0.2.3")


def test_node_file_scan_integration(game_and_agent: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that a when a file is scanned, it's visible health status gets set to the actual health status."""

    game, agent = game_and_agent

    # 1: assert file is healthy
    client_1 = game.simulation.network.get_node_by_hostname("client_1")
    file = client_1.file_system.get_file("downloads", "cat.png")
    assert file.health_status == FileSystemItemHealthStatus.GOOD
    assert file.visible_health_status == FileSystemItemHealthStatus.GOOD

    # 2: perform a scan and make sure nothing has changed
    action = (
        "NODE_FILE_SCAN",
        {
            "node_id": 0,  # client_1,
            "folder_id": 0,  # downloads,
            "file_id": 0,  # cat.png
        },
    )
    agent.store_action(action)
    game.step()

    assert file.health_status == FileSystemItemHealthStatus.GOOD
    assert file.visible_health_status == FileSystemItemHealthStatus.GOOD

    # 3: Set the file to corrupted, and check that only actual updates, not visible.
    file.health_status = FileSystemItemHealthStatus.CORRUPT
    assert file.health_status == FileSystemItemHealthStatus.CORRUPT
    assert file.visible_health_status == FileSystemItemHealthStatus.GOOD

    # 4: Perform a scan and check that it updates
    agent.store_action(action)
    game.step()
    assert file.health_status == FileSystemItemHealthStatus.CORRUPT
    assert file.visible_health_status == FileSystemItemHealthStatus.CORRUPT


def test_node_file_delete_integration(game_and_agent: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that a file can be deleted by the agent."""
    game, agent = game_and_agent

    # 1: assert the file is there
    client_1 = game.simulation.network.get_node_by_hostname("client_1")
    file = client_1.file_system.get_file("downloads", "cat.png")
    assert file is not None
    assert not file.deleted

    # 2: delete the file
    action = (
        "NODE_FILE_DELETE",
        {
            "node_id": 0,  # client_1
            "folder_id": 0,  # downloads
            "file_id": 0,  # cat.png
        },
    )
    agent.store_action(action)
    game.step()

    # 3. Check that the file is not there any more
    assert not client_1.file_system.get_file("downloads", "cat.png")
    # 3.1 (but with the reference to the original file, we can check that deleted flag is True )
    assert file.deleted
