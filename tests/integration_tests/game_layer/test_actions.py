# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
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

from ipaddress import IPv4Address
from typing import Tuple

import pytest
import yaml

from primaite.game.agent.scripted_agents.interface import ProxyAgent
from primaite.game.game import PrimaiteGame
from primaite.session.environment import PrimaiteGymEnv
from primaite.simulator.file_system.file_system_item_abc import FileSystemItemHealthStatus
from primaite.simulator.system.applications.application import ApplicationOperatingState
from primaite.simulator.system.applications.web_browser import WebBrowser
from primaite.simulator.system.software import SoftwareHealthState
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.port import PORT_LOOKUP
from tests import TEST_ASSETS_ROOT

FIREWALL_ACTIONS_NETWORK = TEST_ASSETS_ROOT / "configs/firewall_actions_network.yaml"


def test_do_nothing_integration(game_and_agent: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that the DoNothingAction can form a request and that it is accepted by the simulation."""
    game, agent = game_and_agent

    action = ("DONOTHING", {})
    agent.store_action(action)
    game.step()


def test_node_service_scan_integration(game_and_agent: Tuple[PrimaiteGame, ProxyAgent]):
    """
    Test that the NodeServiceScanAction can form a request and that it is accepted by the simulation.

    The health status of applications is not always updated in the state dict, rather the agent needs to perform a scan.
    Therefore, we set a service to be compromised, check the state is still good, then perform a scan, and check
    that the state changes to the true value.
    """
    game, agent = game_and_agent

    # 1: Check that the service starts off in a good state, and that visible state is hidden until first scan
    svc = game.simulation.network.get_node_by_hostname("server_1").software_manager.software.get("DNSServer")
    assert svc.health_state_actual == SoftwareHealthState.GOOD
    assert svc.health_state_visible == SoftwareHealthState.UNUSED

    # 2: Scan and check that the visible state is now correct
    action = ("NODE_SERVICE_SCAN", {"node_id": 1, "service_id": 0})
    agent.store_action(action)
    game.step()
    assert svc.health_state_actual == SoftwareHealthState.GOOD
    assert svc.health_state_visible == SoftwareHealthState.GOOD

    # 3: Corrupt the service and check that the visible state is still good
    svc.health_state_actual = SoftwareHealthState.COMPROMISED
    assert svc.health_state_visible == SoftwareHealthState.GOOD

    # 4: Scan and check that the visible state is now correct
    action = ("NODE_SERVICE_SCAN", {"node_id": 1, "service_id": 0})
    agent.store_action(action)
    game.step()
    assert svc.health_state_actual == SoftwareHealthState.COMPROMISED
    assert svc.health_state_visible == SoftwareHealthState.COMPROMISED


def test_node_service_fix_integration(game_and_agent: Tuple[PrimaiteGame, ProxyAgent]):
    """
    Test that the NodeServiceFixAction can form a request and that it is accepted by the simulation.

    When you initiate a patch action, the software health state turns to FIXING, then after a few steps, it goes
    to GOOD.
    """
    game, agent = game_and_agent

    # 1: Corrupt the service
    svc = game.simulation.network.get_node_by_hostname("server_1").software_manager.software.get("DNSServer")
    svc.health_state_actual = SoftwareHealthState.COMPROMISED

    # 2: Apply a patch action
    action = ("NODE_SERVICE_FIX", {"node_id": 1, "service_id": 0})
    agent.store_action(action)
    game.step()

    # 3: Check that the service is now in the FIXING state
    assert svc.health_state_actual == SoftwareHealthState.FIXING

    # 4: perform a few do-nothing steps and check that the service is now in the good state
    action = ("DONOTHING", {})
    agent.store_action(action)
    game.step()
    assert svc.health_state_actual == SoftwareHealthState.GOOD


def test_router_acl_addrule_integration(game_and_agent: Tuple[PrimaiteGame, ProxyAgent]):
    """
    Test that the RouterACLAddRuleAction can form a request and that it is accepted by the simulation.

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
        "ROUTER_ACL_ADDRULE",
        {
            "target_router": "router",
            "position": 4,  # 4th rule
            "permission": 2,  # DENY
            "source_ip_id": 3,  # 10.0.1.2 (client_1)
            "dest_ip_id": 6,  # 10.0.2.3 (server_2)
            "dest_port_id": 1,  # ALL
            "source_port_id": 1,  # ALL
            "protocol_id": 1,  # ALL
            "source_wildcard_id": 0,
            "dest_wildcard_id": 0,
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
        "ROUTER_ACL_ADDRULE",
        {
            "target_router": "router",
            "position": 5,  # 5th rule
            "permission": 2,  # DENY
            "source_ip_id": 5,  # 10.0.2.2 (server_1)
            "dest_ip_id": 6,  # 10.0.2.3 (server_2)
            "dest_port_id": 1,  # ALL
            "source_port_id": 1,  # ALL
            "protocol_id": 1,  # ALL
            "source_wildcard_id": 0,
            "dest_wildcard_id": 0,
        },
    )
    agent.store_action(action)
    game.step()

    # 5: Check that the ACL now has 6 rules, but that server_1 can still ping server_2
    assert router.acl.num_rules == 6
    assert server_1.ping("10.0.2.3")  # Can ping server_2


def test_router_acl_removerule_integration(game_and_agent: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that the RouterACLRemoveRuleAction can form a request and that it is accepted by the simulation."""
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
        "ROUTER_ACL_REMOVERULE",
        {
            "target_router": "router",
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


def test_host_nic_disable_integration(game_and_agent: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that the HostNICDisableAction can form a request and that it is accepted by the simulation."""
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
        "HOST_NIC_DISABLE",
        {
            "node_id": 0,  # client_1
            "nic_id": 0,  # the only nic (eth-1)
        },
    )
    agent.store_action(action)
    game.step()

    # 3: Check that the NIC is disabled, and that client 1 cannot access example.com
    assert client_1.network_interface[1].enabled == False
    assert not browser.get_webpage()
    assert not client_1.ping("10.0.2.2")
    assert not client_1.ping("10.0.2.3")

    # 4: check that servers can still communicate
    assert server_1.ping("10.0.2.3")


def test_host_nic_enable_integration(game_and_agent: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that the HostNICEnableAction can form a request and that it is accepted by the simulation."""

    game, agent = game_and_agent

    # 1: Disable client_1 nic
    client_1 = game.simulation.network.get_node_by_hostname("client_1")
    client_1.network_interface[1].disable()
    assert not client_1.ping("10.0.2.2")

    # 2: Use action to enable nic
    action = (
        "HOST_NIC_ENABLE",
        {
            "node_id": 0,  # client_1
            "nic_id": 0,  # the only nic (eth-1)
        },
    )
    agent.store_action(action)
    game.step()

    # 3: Check that the NIC is enabled, and that client 1 can ping again
    assert client_1.network_interface[1].enabled == True
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


def test_node_file_create(game_and_agent: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that a file is created."""
    game, agent = game_and_agent

    client_1 = game.simulation.network.get_node_by_hostname("client_1")  #

    action = (
        "NODE_FILE_CREATE",
        {
            "node_id": 0,
            "folder_name": "test",
            "file_name": "file.txt",
        },
    )
    agent.store_action(action)
    game.step()

    assert client_1.file_system.get_file(folder_name="test", file_name="file.txt")


def test_node_file_access(game_and_agent: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that the file access increments."""
    game, agent = game_and_agent

    client_1 = game.simulation.network.get_node_by_hostname("client_1")  #

    action = (
        "NODE_FILE_CREATE",
        {
            "node_id": 0,
            "folder_name": "test",
            "file_name": "file.txt",
        },
    )
    agent.store_action(action)
    game.step()

    assert client_1.file_system.get_file(folder_name="test", file_name="file.txt").num_access == 0

    action = (
        "NODE_FILE_ACCESS",
        {
            "node_id": 0,
            "folder_name": "test",
            "file_name": "file.txt",
        },
    )
    agent.store_action(action)
    game.step()

    assert client_1.file_system.get_file(folder_name="test", file_name="file.txt").num_access == 1


def test_node_folder_create(game_and_agent: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that a folder is created."""
    game, agent = game_and_agent

    client_1 = game.simulation.network.get_node_by_hostname("client_1")  #

    action = (
        "NODE_FOLDER_CREATE",
        {
            "node_id": 0,
            "folder_name": "test",
        },
    )
    agent.store_action(action)
    game.step()

    assert client_1.file_system.get_folder(folder_name="test")


def test_network_router_port_disable_integration(game_and_agent: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that the NetworkPortDisableAction can form a request and that it is accepted by the simulation."""
    game, agent = game_and_agent

    # 1: Check that client_1 can access the network
    client_1 = game.simulation.network.get_node_by_hostname("client_1")
    server_1 = game.simulation.network.get_node_by_hostname("server_1")
    router = game.simulation.network.get_node_by_hostname("router")

    browser: WebBrowser = client_1.software_manager.software.get("WebBrowser")
    browser.run()
    browser.target_url = "http://www.example.com"
    assert browser.get_webpage()  # check that the browser can access example.com before we block it

    # 2: Disable the NIC on client_1
    action = (
        "NETWORK_PORT_DISABLE",
        {
            "target_nodename": "router",  # router
            "port_id": 1,  # port 1
        },
    )
    agent.store_action(action)
    game.step()

    # 3: Check that the NIC is disabled, and that client 1 cannot access example.com
    assert router.network_interface[1].enabled == False
    assert not browser.get_webpage()
    assert not client_1.ping("10.0.2.2")
    assert not client_1.ping("10.0.2.3")

    # 4: check that servers can still communicate
    assert server_1.ping("10.0.2.3")


def test_network_router_port_enable_integration(game_and_agent: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that the NetworkPortEnableAction can form a request and that it is accepted by the simulation."""

    game, agent = game_and_agent

    # 1: Disable router port 1
    router = game.simulation.network.get_node_by_hostname("router")
    client_1 = game.simulation.network.get_node_by_hostname("client_1")
    router.network_interface[1].disable()
    assert not client_1.ping("10.0.2.2")

    # 2: Use action to enable port
    action = (
        "NETWORK_PORT_ENABLE",
        {
            "target_nodename": "router",  # router
            "port_id": 1,  # port 1
        },
    )
    agent.store_action(action)
    game.step()

    # 3: Check that the Port is enabled, and that client 1 can ping again
    assert router.network_interface[1].enabled == True
    assert client_1.ping("10.0.2.3")


def test_node_application_scan_integration(game_and_agent: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that the NodeApplicationScanAction updates the application status as expected."""
    game, agent = game_and_agent

    # 1: Check that http traffic is going across the network nicely.
    client_1 = game.simulation.network.get_node_by_hostname("client_1")

    browser: WebBrowser = client_1.software_manager.software.get("WebBrowser")
    browser.run()
    browser.target_url = "http://www.example.com"
    assert browser.get_webpage()  # check that the browser can access example.com

    assert browser.health_state_actual == SoftwareHealthState.GOOD
    assert browser.health_state_visible == SoftwareHealthState.UNUSED

    # 2: Scan and check that the visible state is now correct
    action = ("NODE_APPLICATION_SCAN", {"node_id": 0, "application_id": 0})
    agent.store_action(action)
    game.step()
    assert browser.health_state_actual == SoftwareHealthState.GOOD
    assert browser.health_state_visible == SoftwareHealthState.GOOD

    # 3: Corrupt the service and check that the visible state is still good
    browser.health_state_actual = SoftwareHealthState.COMPROMISED
    assert browser.health_state_visible == SoftwareHealthState.GOOD

    # 4: Scan and check that the visible state is now correct
    action = ("NODE_APPLICATION_SCAN", {"node_id": 0, "application_id": 0})
    agent.store_action(action)
    game.step()
    assert browser.health_state_actual == SoftwareHealthState.COMPROMISED
    assert browser.health_state_visible == SoftwareHealthState.COMPROMISED


def test_node_application_fix_integration(game_and_agent: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that the NodeApplicationFixAction can form a request and that it is accepted by the simulation.

    When you initiate a fix action, the software health state turns to FIXING, then after a few steps, it goes
    to GOOD."""
    game, agent = game_and_agent

    # 1: Check that http traffic is going across the network nicely.
    client_1 = game.simulation.network.get_node_by_hostname("client_1")

    browser: WebBrowser = client_1.software_manager.software.get("WebBrowser")
    browser.health_state_actual = SoftwareHealthState.COMPROMISED

    # 2: Apply a fix action
    action = ("NODE_APPLICATION_FIX", {"node_id": 0, "application_id": 0})
    agent.store_action(action)
    game.step()

    # 3: Check that the application is now in the FIXING state
    assert browser.health_state_actual == SoftwareHealthState.FIXING

    # 4: perform a few do-nothing steps and check that the application is now in the good state
    action = ("DONOTHING", {})
    agent.store_action(action)
    game.step()
    assert browser.health_state_actual == SoftwareHealthState.GOOD


def test_node_application_close_integration(game_and_agent: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that the NodeApplicationCloseAction can form a request and that it is accepted by the simulation.

    When you initiate a close action, the Application Operating State changes for CLOSED."""
    game, agent = game_and_agent
    client_1 = game.simulation.network.get_node_by_hostname("client_1")

    browser: WebBrowser = client_1.software_manager.software.get("WebBrowser")
    browser.run()
    assert browser.operating_state == ApplicationOperatingState.RUNNING

    # 2: Apply a close action
    action = ("NODE_APPLICATION_CLOSE", {"node_id": 0, "application_id": 0})
    agent.store_action(action)
    game.step()

    assert browser.operating_state == ApplicationOperatingState.CLOSED


def test_node_application_install_and_uninstall_integration(game_and_agent: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that the NodeApplicationInstallAction and NodeApplicationRemoveAction can form a request and that
    it is accepted by the simulation.

    When you initiate a install action, the Application will be installed and configured on the node.
    The remove action will uninstall the application from the node."""
    game, agent = game_and_agent

    client_1 = game.simulation.network.get_node_by_hostname("client_1")

    assert client_1.software_manager.software.get("DoSBot") is None

    action = ("NODE_APPLICATION_INSTALL", {"node_id": 0, "application_name": "DoSBot"})
    agent.store_action(action)
    game.step()

    assert client_1.software_manager.software.get("DoSBot") is not None

    action = ("NODE_APPLICATION_REMOVE", {"node_id": 0, "application_name": "DoSBot"})
    agent.store_action(action)
    game.step()

    assert client_1.software_manager.software.get("DoSBot") is None


def test_firewall_acl_add_remove_rule_integration():
    """
    Test that FirewallACLAddRuleAction and FirewallACLRemoveRuleAction can form a request and that it is accepted by the simulation.

    Check that all the details of the ACL rules are correctly added to each ACL list of the Firewall.
    Check that rules are removed as expected.
    """
    with open(FIREWALL_ACTIONS_NETWORK, "r") as f:
        cfg = yaml.safe_load(f)

    env = PrimaiteGymEnv(env_config=cfg)

    # 1: Check that traffic is normal and acl starts off with 4 rules.
    firewall = env.game.simulation.network.get_node_by_hostname("firewall")
    assert firewall.internal_inbound_acl.num_rules == 2
    assert firewall.internal_outbound_acl.num_rules == 2
    assert firewall.dmz_inbound_acl.num_rules == 2
    assert firewall.dmz_outbound_acl.num_rules == 2
    assert firewall.external_inbound_acl.num_rules == 1
    assert firewall.external_outbound_acl.num_rules == 1

    env.step(1)  # Add ACL rule to Internal Inbound
    assert firewall.internal_inbound_acl.num_rules == 3
    assert firewall.internal_inbound_acl.acl[1].action.name == "PERMIT"
    assert firewall.internal_inbound_acl.acl[1].src_ip_address == IPv4Address("192.168.0.10")
    assert firewall.internal_inbound_acl.acl[1].dst_ip_address is None
    assert firewall.internal_inbound_acl.acl[1].dst_port is None
    assert firewall.internal_inbound_acl.acl[1].src_port is None
    assert firewall.internal_inbound_acl.acl[1].protocol is None

    env.step(2)  # Remove ACL rule from Internal Inbound
    assert firewall.internal_inbound_acl.num_rules == 2

    env.step(3)  # Add ACL rule to Internal Outbound
    assert firewall.internal_outbound_acl.num_rules == 3
    assert firewall.internal_outbound_acl.acl[1].action.name == "DENY"
    assert firewall.internal_outbound_acl.acl[1].src_ip_address == IPv4Address("192.168.0.10")
    assert firewall.internal_outbound_acl.acl[1].dst_ip_address is None
    assert firewall.internal_outbound_acl.acl[1].dst_port == PORT_LOOKUP["DNS"]
    assert firewall.internal_outbound_acl.acl[1].src_port == PORT_LOOKUP["ARP"]
    assert firewall.internal_outbound_acl.acl[1].protocol == PROTOCOL_LOOKUP["ICMP"]

    env.step(4)  # Remove ACL rule from Internal Outbound
    assert firewall.internal_outbound_acl.num_rules == 2

    env.step(5)  # Add ACL rule to DMZ Inbound
    assert firewall.dmz_inbound_acl.num_rules == 3
    assert firewall.dmz_inbound_acl.acl[1].action.name == "DENY"
    assert firewall.dmz_inbound_acl.acl[1].src_ip_address == IPv4Address("192.168.10.10")
    assert firewall.dmz_inbound_acl.acl[1].dst_ip_address == IPv4Address("192.168.0.10")
    assert firewall.dmz_inbound_acl.acl[1].dst_port == PORT_LOOKUP["HTTP"]
    assert firewall.dmz_inbound_acl.acl[1].src_port == PORT_LOOKUP["HTTP"]
    assert firewall.dmz_inbound_acl.acl[1].protocol == PROTOCOL_LOOKUP["UDP"]

    env.step(6)  # Remove ACL rule from DMZ Inbound
    assert firewall.dmz_inbound_acl.num_rules == 2

    env.step(7)  # Add ACL rule to DMZ Outbound
    assert firewall.dmz_outbound_acl.num_rules == 3
    assert firewall.dmz_outbound_acl.acl[2].action.name == "DENY"
    assert firewall.dmz_outbound_acl.acl[2].src_ip_address == IPv4Address("192.168.10.10")
    assert firewall.dmz_outbound_acl.acl[2].dst_ip_address == IPv4Address("192.168.0.10")
    assert firewall.dmz_outbound_acl.acl[2].dst_port == PORT_LOOKUP["HTTP"]
    assert firewall.dmz_outbound_acl.acl[2].src_port == PORT_LOOKUP["HTTP"]
    assert firewall.dmz_outbound_acl.acl[2].protocol == PROTOCOL_LOOKUP["TCP"]

    env.step(8)  # Remove ACL rule from DMZ Outbound
    assert firewall.dmz_outbound_acl.num_rules == 2

    env.step(9)  # Add ACL rule to External Inbound
    assert firewall.external_inbound_acl.num_rules == 2
    assert firewall.external_inbound_acl.acl[10].action.name == "DENY"
    assert firewall.external_inbound_acl.acl[10].src_ip_address == IPv4Address("192.168.20.10")
    assert firewall.external_inbound_acl.acl[10].dst_ip_address == IPv4Address("192.168.10.10")
    assert firewall.external_inbound_acl.acl[10].dst_port == PORT_LOOKUP["POSTGRES_SERVER"]
    assert firewall.external_inbound_acl.acl[10].src_port == PORT_LOOKUP["POSTGRES_SERVER"]
    assert firewall.external_inbound_acl.acl[10].protocol == PROTOCOL_LOOKUP["ICMP"]

    env.step(10)  # Remove ACL rule from External Inbound
    assert firewall.external_inbound_acl.num_rules == 1

    env.step(11)  # Add ACL rule to External Outbound
    assert firewall.external_outbound_acl.num_rules == 2
    assert firewall.external_outbound_acl.acl[1].action.name == "DENY"
    assert firewall.external_outbound_acl.acl[1].src_ip_address == IPv4Address("192.168.20.10")
    assert firewall.external_outbound_acl.acl[1].dst_ip_address == IPv4Address("192.168.0.10")
    assert firewall.external_outbound_acl.acl[1].dst_port is None
    assert firewall.external_outbound_acl.acl[1].src_port is None
    assert firewall.external_outbound_acl.acl[1].protocol is None

    env.step(12)  # Remove ACL rule from External Outbound
    assert firewall.external_outbound_acl.num_rules == 1


def test_firewall_port_disable_enable_integration():
    """
    Test that NetworkPortEnableAction and NetworkPortDisableAction can form a request and that it is accepted by the simulation.
    """
    with open(FIREWALL_ACTIONS_NETWORK, "r") as f:
        cfg = yaml.safe_load(f)

    env = PrimaiteGymEnv(env_config=cfg)
    firewall = env.game.simulation.network.get_node_by_hostname("firewall")

    assert firewall.dmz_port.enabled == True

    env.step(13)  # Disable Firewall DMZ Port
    assert firewall.dmz_port.enabled == False

    env.step(14)  # Enable Firewall DMZ Port
    assert firewall.dmz_port.enabled == True
