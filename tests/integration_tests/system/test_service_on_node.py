# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from typing import Tuple

import pytest

from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.system.services.service import Service, ServiceOperatingState


@pytest.fixture(scope="function")
def populated_node(
    service_class,
) -> Tuple[Server, Service]:
    server = Server(
        hostname="server",
        ip_address="192.168.0.1",
        subnet_mask="255.255.255.0",
        start_up_duration=0,
        shut_down_duration=0,
    )
    server.power_on()
    server.software_manager.install(service_class)

    service = server.software_manager.software.get("dummy-service")
    service.start()

    return server, service


def test_service_on_offline_node(service_class):
    """Test to check that the service cannot be interacted with when node it is on is off."""
    computer: Computer = Computer(
        hostname="test_computer",
        ip_address="192.168.1.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
        shut_down_duration=0,
    )
    computer.power_on()
    computer.software_manager.install(service_class)

    service: Service = computer.software_manager.software.get("dummy-service")

    computer.power_off()

    assert computer.operating_state is NodeOperatingState.OFF
    assert service.operating_state is ServiceOperatingState.STOPPED

    service.start()
    assert service.operating_state is ServiceOperatingState.STOPPED

    service.resume()
    assert service.operating_state is ServiceOperatingState.STOPPED

    service.restart()
    assert service.operating_state is ServiceOperatingState.STOPPED

    service.pause()
    assert service.operating_state is ServiceOperatingState.STOPPED


def test_server_turns_off_service(populated_node):
    """Check that the service is turned off when the server is turned off"""
    server, service = populated_node

    assert server.operating_state is NodeOperatingState.ON
    assert service.operating_state is ServiceOperatingState.RUNNING

    server.power_off()

    assert server.operating_state is NodeOperatingState.OFF
    assert service.operating_state is ServiceOperatingState.STOPPED


def test_service_cannot_be_turned_on_when_server_is_off(populated_node):
    """Check that the service cannot be started when the server is off."""
    server, service = populated_node

    assert server.operating_state is NodeOperatingState.ON
    assert service.operating_state is ServiceOperatingState.RUNNING

    server.power_off()

    assert server.operating_state is NodeOperatingState.OFF
    assert service.operating_state is ServiceOperatingState.STOPPED

    service.start()

    assert server.operating_state is NodeOperatingState.OFF
    assert service.operating_state is ServiceOperatingState.STOPPED


def test_server_turns_on_service(populated_node):
    """Check that turning on the server turns on service."""
    server, service = populated_node

    assert server.operating_state is NodeOperatingState.ON
    assert service.operating_state is ServiceOperatingState.RUNNING

    server.power_off()

    assert server.operating_state is NodeOperatingState.OFF
    assert service.operating_state is ServiceOperatingState.STOPPED

    server.power_on()

    assert server.operating_state is NodeOperatingState.ON
    assert service.operating_state is ServiceOperatingState.RUNNING

    server.power_off()

    assert server.operating_state is NodeOperatingState.OFF
    assert service.operating_state is ServiceOperatingState.STOPPED

    server.power_on()

    assert server.operating_state is NodeOperatingState.ON
    assert service.operating_state is ServiceOperatingState.RUNNING
