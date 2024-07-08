# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from typing import Tuple

import pytest

from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.system.applications.application import Application, ApplicationOperatingState


@pytest.fixture(scope="function")
def populated_node(application_class) -> Tuple[Application, Computer]:
    computer: Computer = Computer(
        hostname="test_computer",
        ip_address="192.168.1.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
        shut_down_duration=0,
    )
    computer.power_on()
    computer.software_manager.install(application_class)

    app = computer.software_manager.software.get("DummyApplication")
    app.run()

    return app, computer


def test_application_on_offline_node(application_class):
    """Test to check that the application cannot be interacted with when node it is on is off."""
    computer: Computer = Computer(
        hostname="test_computer",
        ip_address="192.168.1.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
        shut_down_duration=0,
    )
    computer.software_manager.install(application_class)

    app: Application = computer.software_manager.software.get("DummyApplication")

    computer.power_off()

    assert computer.operating_state is NodeOperatingState.OFF
    assert app.operating_state is ApplicationOperatingState.CLOSED

    app.run()
    assert app.operating_state is ApplicationOperatingState.CLOSED


def test_server_turns_off_application(populated_node):
    """Check that the application is turned off when the server is turned off"""
    app, computer = populated_node

    assert computer.operating_state is NodeOperatingState.ON
    assert app.operating_state is ApplicationOperatingState.RUNNING

    computer.power_off()

    assert computer.operating_state is NodeOperatingState.OFF
    assert app.operating_state is ApplicationOperatingState.CLOSED


def test_application_cannot_be_turned_on_when_computer_is_off(populated_node):
    """Check that the application cannot be started when the computer is off."""
    app, computer = populated_node

    assert computer.operating_state is NodeOperatingState.ON
    assert app.operating_state is ApplicationOperatingState.RUNNING

    computer.power_off()

    assert computer.operating_state is NodeOperatingState.OFF
    assert app.operating_state is ApplicationOperatingState.CLOSED

    app.run()

    assert computer.operating_state is NodeOperatingState.OFF
    assert app.operating_state is ApplicationOperatingState.CLOSED


def test_computer_runs_applications(populated_node):
    """Check that turning on the computer will turn on applications."""
    app, computer = populated_node

    assert computer.operating_state is NodeOperatingState.ON
    assert app.operating_state is ApplicationOperatingState.RUNNING

    computer.power_off()

    assert computer.operating_state is NodeOperatingState.OFF
    assert app.operating_state is ApplicationOperatingState.CLOSED

    computer.power_on()

    assert computer.operating_state is NodeOperatingState.ON
    assert app.operating_state is ApplicationOperatingState.RUNNING

    computer.power_off()

    assert computer.operating_state is NodeOperatingState.OFF
    assert app.operating_state is ApplicationOperatingState.CLOSED

    computer.power_on()

    assert computer.operating_state is NodeOperatingState.ON
    assert app.operating_state is ApplicationOperatingState.RUNNING
