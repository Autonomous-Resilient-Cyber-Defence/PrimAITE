# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from typing import Tuple

import pytest

from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.network.switch import Switch
from primaite.simulator.network.protocols.ssh import SSHConnectionMessage, SSHPacket, SSHTransportMessage
from primaite.simulator.system.services.service import ServiceOperatingState
from primaite.simulator.system.services.terminal.terminal import Terminal
from primaite.simulator.system.software import SoftwareHealthState


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

    payload: SSHPacket = SSHPacket(
        payload="Test_Payload",
        transport_message=SSHTransportMessage.SSH_MSG_SERVICE_REQUEST,
        connection_message=SSHConnectionMessage.SSH_MSG_CHANNEL_OPEN,
    )

    assert terminal_a.send(payload=payload, dest_ip_address="192.168.0.11")


def test_terminal_fail_when_closed(basic_network):
    """Ensure Terminal won't attempt to send/receive when off"""
    network: Network = basic_network
    computer: Computer = network.get_node_by_hostname("node_a")
    terminal: Terminal = computer.software_manager.software.get("Terminal")

    terminal.operating_state = ServiceOperatingState.STOPPED

    assert terminal.login(dest_ip_address="192.168.0.11") is False


def test_terminal_disconnect(basic_network):
    """Terminal should set is_connected to false on disconnect"""
    network: Network = basic_network
    computer: Computer = network.get_node_by_hostname("node_a")
    terminal: Terminal = computer.software_manager.software.get("Terminal")

    assert terminal.is_connected is False

    terminal.login(dest_ip_address="192.168.0.11")

    assert terminal.is_connected is True

    terminal.disconnect(dest_ip_address="192.168.0.11")

    assert terminal.is_connected is False


def test_terminal_ignores_when_off(basic_network):
    """Terminal should ignore commands when not running"""
    network: Network = basic_network
    computer_a: Computer = network.get_node_by_hostname("node_a")
    terminal_a: Terminal = computer_a.software_manager.software.get("Terminal")

    computer_b: Computer = network.get_node_by_hostname("node_b")

    terminal_a.login(dest_ip_address="192.168.0.11")  # login to computer_b

    assert terminal_a.is_connected is True

    terminal_a.operating_state = ServiceOperatingState.STOPPED

    payload: SSHPacket = SSHPacket(
        payload="Test_Payload",
        transport_message=SSHTransportMessage.SSH_MSG_SERVICE_REQUEST,
        connection_message=SSHConnectionMessage.SSH_MSG_CHANNEL_DATA,
    )

    assert not terminal_a.send(payload=payload, dest_ip_address="192.168.0.11")
