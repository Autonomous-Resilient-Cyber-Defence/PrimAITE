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
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.hardware.nodes.network.router import ACLAction, Router
from primaite.simulator.network.hardware.nodes.network.switch import Switch
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.sim_container import Simulation
from primaite.simulator.system.applications.web_browser import WebBrowser
from primaite.simulator.system.services.dns.dns_client import DNSClient
from primaite.simulator.system.services.dns.dns_server import DNSServer
from primaite.simulator.system.services.web_server.web_server import WebServer
from primaite.simulator.system.software import SoftwareHealthState


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
    assert client_1.network_interface[1].enabled == False
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
    client_1.network_interface[1].disable()
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
