# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from typing import Tuple

import pytest

from primaite.game.agent.interface import ProxyAgent
from primaite.game.game import PrimaiteGame
from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.hardware.nodes.network.router import ACLAction, Router
from primaite.simulator.network.hardware.nodes.network.switch import Switch
from primaite.simulator.network.protocols.ssh import SSHConnectionMessage, SSHPacket, SSHTransportMessage
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.services.dns.dns_server import DNSServer
from primaite.simulator.system.services.service import ServiceOperatingState
from primaite.simulator.system.services.terminal.terminal import Terminal
from primaite.simulator.system.services.web_server.web_server import WebServer


@pytest.fixture(scope="function")
def terminal_on_computer() -> Tuple[Terminal, Computer]:
    computer: Computer = Computer(
        hostname="node_a", ip_address="192.168.0.10", subnet_mask="255.255.255.0", start_up_duration=0
    )
    computer.power_on()
    terminal: Terminal = computer.software_manager.software.get("Terminal")

    return [terminal, computer]


@pytest.fixture(scope="function")
def basic_network() -> Network:
    network = Network()
    node_a = Computer(hostname="node_a", ip_address="192.168.0.10", subnet_mask="255.255.255.0", start_up_duration=0)
    node_a.power_on()
    node_a.software_manager.get_open_ports()

    node_b = Computer(hostname="node_b", ip_address="192.168.0.11", subnet_mask="255.255.255.0", start_up_duration=0)
    node_b.power_on()
    network.connect(node_a.network_interface[1], node_b.network_interface[1])

    return network


def test_terminal_creation(terminal_on_computer):
    terminal, computer = terminal_on_computer
    terminal.describe_state()


def test_terminal_install_default():
    """Terminal should be auto installed onto Nodes"""
    computer = Computer(hostname="node_a", ip_address="192.168.0.10", subnet_mask="255.255.255.0", start_up_duration=0)
    computer.power_on()

    assert computer.software_manager.software.get("Terminal")


def test_terminal_not_on_switch():
    """Ensure terminal does not auto-install to switch"""
    test_switch = Switch(hostname="Test")

    assert not test_switch.software_manager.software.get("Terminal")


def test_terminal_send(basic_network):
    """Check that Terminal can send"""
    network: Network = basic_network
    computer_a: Computer = network.get_node_by_hostname("node_a")
    terminal_a: Terminal = computer_a.software_manager.software.get("Terminal")
    computer_b: Computer = network.get_node_by_hostname("node_b")

    payload: SSHPacket = SSHPacket(
        payload="Test_Payload",
        transport_message=SSHTransportMessage.SSH_MSG_SERVICE_REQUEST,
        connection_message=SSHConnectionMessage.SSH_MSG_CHANNEL_OPEN,
        sender_ip_address=computer_a.network_interface[1].ip_address,
        target_ip_address=computer_b.network_interface[1].ip_address,
    )

    assert terminal_a.send(payload=payload, dest_ip_address=computer_b.network_interface[1].ip_address)


def test_terminal_fail_when_closed(basic_network):
    """Ensure Terminal won't attempt to send/receive when off"""
    network: Network = basic_network
    computer: Computer = network.get_node_by_hostname("node_a")
    terminal: Terminal = computer.software_manager.software.get("Terminal")
    computer_b: Computer = network.get_node_by_hostname("node_b")

    terminal.operating_state = ServiceOperatingState.STOPPED

    assert (
        terminal.login(username="admin", password="Admin123!", ip_address=computer_b.network_interface[1].ip_address)
        is False
    )


def test_terminal_disconnect(basic_network):
    """Terminal should set is_connected to false on disconnect"""
    network: Network = basic_network
    computer_a: Computer = network.get_node_by_hostname("node_a")
    terminal_a: Terminal = computer_a.software_manager.software.get("Terminal")
    computer_b: Computer = network.get_node_by_hostname("node_b")
    terminal_b: Terminal = computer_b.software_manager.software.get("Terminal")

    assert terminal_a.is_connected is False

    terminal_a.login(username="admin", password="Admin123!", ip_address=computer_b.network_interface[1].ip_address)

    assert terminal_a.is_connected is True

    terminal_a.disconnect(dest_ip_address=computer_b.network_interface[1].ip_address)

    assert terminal_a.is_connected is False


def test_terminal_ignores_when_off(basic_network):
    """Terminal should ignore commands when not running"""
    network: Network = basic_network
    computer_a: Computer = network.get_node_by_hostname("node_a")
    terminal_a: Terminal = computer_a.software_manager.software.get("Terminal")

    computer_b: Computer = network.get_node_by_hostname("node_b")

    terminal_a.login(username="admin", password="Admin123!", ip_address="192.168.0.11")  # login to computer_b

    assert terminal_a.is_connected is True

    terminal_a.operating_state = ServiceOperatingState.STOPPED

    payload: SSHPacket = SSHPacket(
        payload="Test_Payload",
        transport_message=SSHTransportMessage.SSH_MSG_SERVICE_REQUEST,
        connection_message=SSHConnectionMessage.SSH_MSG_CHANNEL_DATA,
        sender_ip_address=computer_a.network_interface[1].ip_address,
        target_ip_address="192.168.0.11",
    )

    assert not terminal_a.send(payload=payload, dest_ip_address="192.168.0.11")


def test_terminal_acknowledges_acl_rules(basic_network):
    """Test that Terminal messages"""

    network: Network = basic_network
    computer_a: Computer = network.get_node_by_hostname("node_a")
    terminal_a: Terminal = computer_a.software_manager.software.get("Terminal")

    terminal_a.login(username="admin", password="Admin123!", ip_address="192.168.0.11")

    router = Router(hostname="router", num_ports=3, start_up_duration=0)
    router.power_on()
    router.configure_port(port=1, ip_address="10.0.1.1", subnet_mask="255.255.255.0")
    router.configure_port(port=2, ip_address="10.0.2.1", subnet_mask="255.255.255.0")

    router.acl.add_rule(action=ACLAction.DENY, src_port=Port.SSH, dst_port=Port.SSH, position=22)


def test_network_simulation(basic_network):
    # 0: Pull out the network
    network = basic_network

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

    client_2 = Computer(
        hostname="client_2",
        ip_address="10.0.2.2",
        subnet_mask="255.255.255.0",
    )
    client_2.power_on()
    network.connect(endpoint_a=client_2.network_interface[1], endpoint_b=switch_2.network_interface[1])

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
    router.acl.add_rule(action=ACLAction.DENY, src_port=Port.ARP, dst_port=Port.ARP, position=22)
    router.acl.add_rule(action=ACLAction.DENY, protocol=IPProtocol.ICMP, position=23)
    router.acl.add_rule(action=ACLAction.DENY, src_port=Port.DNS, dst_port=Port.DNS, position=1)
    router.acl.add_rule(action=ACLAction.DENY, src_port=Port.HTTP, dst_port=Port.HTTP, position=3)

    # 3: Install server software
    server_1.software_manager.install(DNSServer)
    dns_service: DNSServer = server_1.software_manager.software.get("DNSServer")  # noqa
    dns_service.dns_register("www.example.com", server_2.network_interface[1].ip_address)
    server_2.software_manager.install(WebServer)

    # 3.1: Ensure that the dns clients are configured correctly
    client_1.software_manager.software.get("DNSClient").dns_server = server_1.network_interface[1].ip_address
    server_2.software_manager.software.get("DNSClient").dns_server = server_1.network_interface[1].ip_address

    terminal_1: Terminal = client_1.software_manager.software.get("Terminal")

    assert terminal_1.login(username="admin", password="Admin123!", ip_address="10.0.2.2") is False


def test_terminal_receives_requests(game_and_agent_fixture: Tuple[PrimaiteGame, ProxyAgent]):
    game, agent = game_and_agent_fixture

    network: Network = game.simulation.network
    computer_a: Computer = network.get_node_by_hostname("node_a")
    terminal_a: Terminal = computer_a.software_manager.software.get("Terminal")

    computer_b: Computer = network.get_node_by_hostname("node_b")

    assert terminal_a.is_connected is False

    action = ("TERMINAL_LOGIN", {"username": "admin", "password": "Admin123!"})  # TODO: Add Action to ActionManager ?

    agent.store_action(action)
    game.step()

    assert terminal_a.is_connected is True
