# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from typing import Tuple
from uuid import uuid4

import pytest

from primaite.game.agent.interface import ProxyAgent
from primaite.game.game import PrimaiteGame
from primaite.interface.request import RequestResponse
from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.hardware.nodes.network.router import ACLAction, Router
from primaite.simulator.network.hardware.nodes.network.switch import Switch
from primaite.simulator.network.hardware.nodes.network.wireless_router import WirelessRouter
from primaite.simulator.network.networks import arcd_uc2_network
from primaite.simulator.network.protocols.ssh import (
    SSHConnectionMessage,
    SSHPacket,
    SSHTransportMessage,
    SSHUserCredentials,
)
from primaite.simulator.system.applications.red_applications.ransomware_script import RansomwareScript
from primaite.simulator.system.services.dns.dns_server import DNSServer
from primaite.simulator.system.services.service import ServiceOperatingState
from primaite.simulator.system.services.terminal.terminal import RemoteTerminalConnection, Terminal
from primaite.simulator.system.services.web_server.web_server import WebServer
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.port import PORT_LOOKUP


@pytest.fixture(scope="function")
def terminal_on_computer() -> Tuple[Terminal, Computer]:
    computer: Computer = Computer.from_config(
        config={
            "type": "computer",
            "hostname": "node_a",
            "ip_address": "192.168.0.10",
            "subnet_mask": "255.255.255.0",
            "start_up_duration": 0,
        }
    )
    computer.power_on()
    terminal: Terminal = computer.software_manager.software.get("terminal")

    return terminal, computer


@pytest.fixture(scope="function")
def basic_network() -> Network:
    network = Network()
    node_a = Computer.from_config(
        config={
            "type": "computer",
            "hostname": "node_a",
            "ip_address": "192.168.0.10",
            "subnet_mask": "255.255.255.0",
            "start_up_duration": 0,
        }
    )
    node_a.power_on()
    node_a.software_manager.get_open_ports()

    node_b = Computer.from_config(
        config={
            "type": "computer",
            "hostname": "node_b",
            "ip_address": "192.168.0.11",
            "subnet_mask": "255.255.255.0",
            "start_up_duration": 0,
        }
    )
    node_b.power_on()
    network.connect(node_a.network_interface[1], node_b.network_interface[1])

    return network


@pytest.fixture(scope="function")
def wireless_wan_network():
    network = Network()

    # Configure PC A
    pc_a_cfg = {
        "type": "computer",
        "hostname": "pc_a",
        "ip_address": "192.168.0.2",
        "subnet_mask": "255.255.255.0",
        "default_gateway": "192.168.0.1",
        "start_up_duration": 0,
    }

    pc_a = Computer.from_config(config=pc_a_cfg)
    pc_a.power_on()
    network.add_node(pc_a)

    # Configure Router 1
    router_1 = WirelessRouter.from_config(
        config={"type": "wireless-router", "hostname": "router_1", "start_up_duration": 0}, airspace=network.airspace
    )
    router_1.power_on()
    network.add_node(router_1)

    # Configure the connection between PC A and Router 1 port 2
    router_1.configure_router_interface("192.168.0.1", "255.255.255.0")
    network.connect(pc_a.network_interface[1], router_1.network_interface[2])

    # Configure Router 1 ACLs
    router_1.acl.add_rule(
        action=ACLAction.PERMIT, src_port=PORT_LOOKUP["ARP"], dst_port=PORT_LOOKUP["ARP"], position=22
    )
    router_1.acl.add_rule(action=ACLAction.PERMIT, protocol=PROTOCOL_LOOKUP["ICMP"], position=23)

    # add acl rule to allow SSH traffic
    router_1.acl.add_rule(
        action=ACLAction.PERMIT, src_port=PORT_LOOKUP["SSH"], dst_port=PORT_LOOKUP["SSH"], position=21
    )

    # Configure PC B

    pc_b_cfg = {
        "type": "computer",
        "hostname": "pc_b",
        "ip_address": "192.168.2.2",
        "subnet_mask": "255.255.255.0",
        "default_gateway": "192.168.2.1",
        "start_up_duration": 0,
    }

    pc_b = Computer.from_config(config=pc_b_cfg)
    pc_b.power_on()
    network.add_node(pc_b)

    # Configure Router 2 ACLs

    # Configure the wireless connection between Router 1 port 1 and Router 2 port 1
    router_1.configure_wireless_access_point("192.168.1.1", "255.255.255.0")

    router_1.route_table.add_route(
        address="192.168.2.0", subnet_mask="255.255.255.0", next_hop_ip_address="192.168.1.2"
    )

    return network


@pytest.fixture
def game_and_agent_fixture(game_and_agent):
    """Create a game with a simple agent that can be controlled by the tests."""
    game, agent = game_and_agent

    client_1: Computer = game.simulation.network.get_node_by_hostname("client_1")
    client_1.config.start_up_duration = 3

    return game, agent


def test_terminal_creation(terminal_on_computer):
    terminal, computer = terminal_on_computer
    terminal.describe_state()


def test_terminal_install_default():
    """Terminal should be auto installed onto Nodes"""
    computer: Computer = Computer.from_config(
        config={
            "type": "computer",
            "hostname": "node_a",
            "ip_address": "192.168.0.10",
            "subnet_mask": "255.255.255.0",
            "start_up_duration": 0,
        }
    )
    computer.power_on()

    assert computer.software_manager.software.get("terminal")


def test_terminal_not_on_switch():
    """Ensure terminal does not auto-install to switch"""
    test_switch = Switch.from_config(config={"type": "switch", "hostname": "Test"})

    assert not test_switch.software_manager.software.get("terminal")


def test_terminal_send(basic_network):
    """Test that terminal can send valid commands."""
    network: Network = basic_network
    computer_a: Computer = network.get_node_by_hostname("node_a")
    terminal_a: Terminal = computer_a.software_manager.software.get("terminal")
    computer_b: Computer = network.get_node_by_hostname("node_b")

    payload: SSHPacket = SSHPacket(
        payload="Test_Payload",
        transport_message=SSHTransportMessage.SSH_MSG_USERAUTH_REQUEST,
        connection_message=SSHConnectionMessage.SSH_MSG_CHANNEL_DATA,
        user_account=SSHUserCredentials(username="username", password="password"),
        connection_request_uuid=str(uuid4()),
    )

    assert terminal_a.send(payload=payload, dest_ip_address=computer_b.network_interface[1].ip_address)


def test_terminal_receive(basic_network):
    """Test that terminal can receive and process commands"""
    network: Network = basic_network
    computer_a: Computer = network.get_node_by_hostname("node_a")
    terminal_a: Terminal = computer_a.software_manager.software.get("terminal")
    computer_b: Computer = network.get_node_by_hostname("node_b")
    folder_name = "Downloads"

    payload: SSHPacket = SSHPacket(
        payload=["file_system", "create", "folder", folder_name],
        transport_message=SSHTransportMessage.SSH_MSG_SERVICE_REQUEST,
        connection_message=SSHConnectionMessage.SSH_MSG_CHANNEL_OPEN,
    )

    term_a_on_node_b: RemoteTerminalConnection = terminal_a.login(
        username="admin", password="admin", ip_address="192.168.0.11"
    )

    term_a_on_node_b.execute(["file_system", "create", "folder", folder_name])

    # Assert that the Folder has been correctly created
    assert computer_b.file_system.get_folder(folder_name)


def test_terminal_install(basic_network):
    """Test that terminal can successfully process an INSTALL request"""
    network: Network = basic_network
    computer_a: Computer = network.get_node_by_hostname("node_a")
    terminal_a: Terminal = computer_a.software_manager.software.get("terminal")
    computer_b: Computer = network.get_node_by_hostname("node_b")

    payload: SSHPacket = SSHPacket(
        payload=["software_manager", "application", "install", "ransomware-script"],
        transport_message=SSHTransportMessage.SSH_MSG_SERVICE_REQUEST,
        connection_message=SSHConnectionMessage.SSH_MSG_CHANNEL_OPEN,
    )

    term_a_on_node_b: RemoteTerminalConnection = terminal_a.login(
        username="admin", password="admin", ip_address="192.168.0.11"
    )

    term_a_on_node_b.execute(["software_manager", "application", "install", "ransomware-script"])

    assert computer_b.software_manager.software.get("ransomware-script")


def test_terminal_fail_when_closed(basic_network):
    """Ensure terminal won't attempt to send/receive when off"""
    network: Network = basic_network
    computer: Computer = network.get_node_by_hostname("node_a")
    terminal: Terminal = computer.software_manager.software.get("terminal")
    computer_b: Computer = network.get_node_by_hostname("node_b")

    terminal.operating_state = ServiceOperatingState.STOPPED

    assert not terminal.login(username="admin", password="admin", ip_address=computer_b.network_interface[1].ip_address)


def test_terminal_disconnect(basic_network):
    """Test terminal disconnects"""
    network: Network = basic_network
    computer_a: Computer = network.get_node_by_hostname("node_a")
    terminal_a: Terminal = computer_a.software_manager.software.get("terminal")
    computer_b: Computer = network.get_node_by_hostname("node_b")
    terminal_b: Terminal = computer_b.software_manager.software.get("terminal")

    assert len(terminal_b._connections) == 0

    term_a_on_term_b = terminal_a.login(
        username="admin", password="admin", ip_address=computer_b.network_interface[1].ip_address
    )

    assert len(terminal_b._connections) == 1

    term_a_on_term_b.disconnect()

    assert len(terminal_b._connections) == 0

    assert term_a_on_term_b.is_active is False


def test_terminal_ignores_when_off(basic_network):
    """terminal should ignore commands when not running"""
    network: Network = basic_network
    computer_a: Computer = network.get_node_by_hostname("node_a")
    terminal_a: Terminal = computer_a.software_manager.software.get("terminal")

    computer_b: Computer = network.get_node_by_hostname("node_b")

    term_a_on_term_b: RemoteTerminalConnection = terminal_a.login(
        username="admin", password="admin", ip_address="192.168.0.11"
    )  # login to computer_b

    terminal_a.operating_state = ServiceOperatingState.STOPPED

    assert not term_a_on_term_b.execute(["software_manager", "application", "install", "ransomware-script"])


def test_computer_remote_login_to_router(wireless_wan_network):
    """Test to confirm that a computer can SSH into a router."""

    pc_a = wireless_wan_network.get_node_by_hostname("pc_a")

    router_1 = wireless_wan_network.get_node_by_hostname("router_1")

    pc_a_terminal: Terminal = pc_a.software_manager.software.get("terminal")

    assert len(pc_a_terminal._connections) == 0

    pc_a_on_router_1 = pc_a_terminal.login(username="admin", password="admin", ip_address="192.168.1.1")

    assert len(pc_a_terminal._connections) == 1

    payload = ["software_manager", "application", "install", "ransomware-script"]

    pc_a_on_router_1.execute(payload)

    assert router_1.software_manager.software.get("ransomware-script")


def test_router_remote_login_to_computer(wireless_wan_network):
    """Test to confirm that a router can ssh into a computer."""
    pc_a = wireless_wan_network.get_node_by_hostname("pc_a")

    router_1 = wireless_wan_network.get_node_by_hostname("router_1")

    router_1_terminal: Terminal = router_1.software_manager.software.get("terminal")

    assert len(router_1_terminal._connections) == 0

    router_1_on_pc_a = router_1_terminal.login(username="admin", password="admin", ip_address="192.168.0.2")

    assert len(router_1_terminal._connections) == 1

    payload = ["software_manager", "application", "install", "ransomware-script"]

    router_1_on_pc_a.execute(payload)

    assert pc_a.software_manager.software.get("ransomware-script")


def test_router_blocks_SSH_traffic(wireless_wan_network):
    """Test to check that router will block SSH traffic if no ACL rule."""
    pc_a = wireless_wan_network.get_node_by_hostname("pc_a")

    router_1 = wireless_wan_network.get_node_by_hostname("router_1")

    # Remove rule that allows SSH traffic.
    router_1.acl.remove_rule(position=21)

    pc_a_terminal: Terminal = pc_a.software_manager.software.get("terminal")

    assert len(pc_a_terminal._connections) == 0

    pc_a_terminal.login(username="admin", password="admin", ip_address="192.168.0.2")

    assert len(pc_a_terminal._connections) == 0


def test_SSH_across_network():
    """Test to show ability to SSH across a network."""
    network: Network = arcd_uc2_network()
    pc_a = network.get_node_by_hostname("client_1")
    router_1 = network.get_node_by_hostname("router_1")

    terminal_a: Terminal = pc_a.software_manager.software.get("terminal")

    router_1.acl.add_rule(
        action=ACLAction.PERMIT, src_port=PORT_LOOKUP["SSH"], dst_port=PORT_LOOKUP["SSH"], position=21
    )

    assert len(terminal_a._connections) == 0

    # Login to the Domain Controller
    terminal_a.login(username="admin", password="admin", ip_address="192.168.1.10")

    assert len(terminal_a._connections) == 1


def test_multiple_remote_terminals_same_node(basic_network):
    """Test to check that multiple remote terminals can be spawned by one node."""
    network: Network = basic_network
    computer_a: Computer = network.get_node_by_hostname("node_a")
    terminal_a: Terminal = computer_a.software_manager.software.get("terminal")
    computer_b: Computer = network.get_node_by_hostname("node_b")

    assert len(terminal_a._connections) == 0

    # Spam login requests to node.
    for attempt in range(3):
        remote_connection = terminal_a.login(username="admin", password="admin", ip_address="192.168.0.11")

    assert len(terminal_a._connections) == 3


def test_terminal_rejects_commands_if_disconnect(basic_network):
    """Test to check terminal will ignore commands from disconnected connections"""
    network: Network = basic_network
    computer_a: Computer = network.get_node_by_hostname("node_a")
    terminal_a: Terminal = computer_a.software_manager.software.get("terminal")
    computer_b: Computer = network.get_node_by_hostname("node_b")

    terminal_b: Terminal = computer_b.software_manager.software.get("terminal")

    remote_connection = terminal_a.login(username="admin", password="admin", ip_address="192.168.0.11")

    assert len(terminal_a._connections) == 1
    assert len(terminal_b._connections) == 1

    remote_connection.disconnect()

    assert len(terminal_a._connections) == 0
    assert len(terminal_b._connections) == 0

    assert remote_connection.execute(["software_manager", "application", "install", "ransomware-script"]) is False

    assert not computer_b.software_manager.software.get("ransomware-script")

    assert remote_connection.is_active is False


def test_terminal_connection_timeout(basic_network):
    """Test that terminal_connections are affected by UserSession timeout."""
    network: Network = basic_network
    computer_a: Computer = network.get_node_by_hostname("node_a")
    terminal_a: Terminal = computer_a.software_manager.software.get("terminal")
    computer_b: Computer = network.get_node_by_hostname("node_b")
    terminal_b: Terminal = computer_b.software_manager.software.get("terminal")

    remote_connection = terminal_a.login(username="admin", password="admin", ip_address="192.168.0.11")

    assert len(terminal_a._connections) == 1
    assert len(terminal_b._connections) == 1
    assert len(computer_b.user_session_manager.remote_sessions) == 1

    remote_session = computer_b.user_session_manager.remote_sessions[remote_connection.connection_uuid]
    computer_b.user_session_manager._timeout_session(remote_session)

    assert len(terminal_a._connections) == 0
    assert len(terminal_b._connections) == 0
    assert len(computer_b.user_session_manager.remote_sessions) == 0

    assert not remote_connection.is_active


def test_terminal_last_response_updates(basic_network):
    """Test that the _last_response within Terminal correctly updates."""
    network: Network = basic_network
    computer_a: Computer = network.get_node_by_hostname("node_a")
    terminal_a: Terminal = computer_a.software_manager.software.get("terminal")
    computer_b: Computer = network.get_node_by_hostname("node_b")

    assert terminal_a.last_response is None

    remote_connection = terminal_a.login(username="admin", password="admin", ip_address="192.168.0.11")

    # Last response should be a successful logon
    assert terminal_a.last_response == RequestResponse(status="success", data={"reason": "Login Successful"})

    remote_connection.execute(command=["software_manager", "application", "install", "ransomware-script"])

    # Last response should now update following successful install
    assert terminal_a.last_response == RequestResponse(status="success", data={})

    remote_connection.execute(command=["software_manager", "application", "install", "ransomware-script"])

    # Last response should now update to success, but with supplied reason.
    assert terminal_a.last_response == RequestResponse(status="success", data={"reason": "already installed"})

    remote_connection.execute(command=["file_system", "create", "file", "folder123", "doggo.pdf", False])

    # Check file was created.
    assert computer_b.file_system.access_file(folder_name="folder123", file_name="doggo.pdf")

    # Last response should be confirmation of file creation.
    assert terminal_a.last_response == RequestResponse(
        status="success",
        data={"file_name": "doggo.pdf", "folder_name": "folder123", "file_type": "PDF", "file_size": 102400},
    )

    remote_connection.execute(
        command=[
            "service",
            "ftp-client",
            "send",
            {
                "dest_ip_address": "192.168.0.2",
                "src_folder": "folder123",
                "src_file_name": "cat.pdf",
                "dest_folder": "root",
                "dest_file_name": "cat.pdf",
            },
        ]
    )

    assert terminal_a.last_response == RequestResponse(
        status="failure",
        data={"reason": "Unable to locate given file on local file system. Perhaps given options are invalid?"},
    )
