from typing import Tuple

import pytest

from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.computer import Computer
from primaite.simulator.system.applications.application import Application, ApplicationOperatingState


@pytest.fixture(scope="function")
def populated_node(application_class) -> Tuple[Application, Computer]:
    computer: Computer = Computer(
        hostname="test_computer",
        ip_address="192.168.1.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        operating_state=NodeOperatingState.ON,
    )
    computer.software_manager.install(application_class)

    app = computer.software_manager.software["TestApplication"]
    app.run()

    return app, computer


def test_service_on_offline_node(application_class):
    """Test to check that the service cannot be interacted with when node it is on is off."""
    computer: Computer = Computer(
        hostname="test_computer",
        ip_address="192.168.1.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        operating_state=NodeOperatingState.ON,
    )
    computer.software_manager.install(application_class)

    app: Application = computer.software_manager.software["TestApplication"]

    computer.power_off()

    for i in range(computer.shut_down_duration + 1):
        computer.apply_timestep(timestep=i)

    assert computer.operating_state is NodeOperatingState.OFF
    assert app.operating_state is ApplicationOperatingState.CLOSED

    app.run()
    assert app.operating_state is ApplicationOperatingState.CLOSED


def test_server_turns_off_service(populated_node):
    """Check that the service is turned off when the server is turned off"""
    app, computer = populated_node

    assert computer.operating_state is NodeOperatingState.ON
    assert app.operating_state is ApplicationOperatingState.RUNNING

    computer.power_off()

    for i in range(computer.shut_down_duration + 1):
        computer.apply_timestep(timestep=i)

    assert computer.operating_state is NodeOperatingState.OFF
    assert app.operating_state is ApplicationOperatingState.CLOSED


def test_service_cannot_be_turned_on_when_server_is_off(populated_node):
    """Check that the service cannot be started when the server is off."""
    app, computer = populated_node

    assert computer.operating_state is NodeOperatingState.ON
    assert app.operating_state is ApplicationOperatingState.RUNNING

    computer.power_off()

    for i in range(computer.shut_down_duration + 1):
        computer.apply_timestep(timestep=i)

    assert computer.operating_state is NodeOperatingState.OFF
    assert app.operating_state is ApplicationOperatingState.CLOSED

    app.run()

    assert computer.operating_state is NodeOperatingState.OFF
    assert app.operating_state is ApplicationOperatingState.CLOSED


def test_server_turns_on_service(populated_node):
    """Check that turning on the server turns on service."""
    app, computer = populated_node

    assert computer.operating_state is NodeOperatingState.ON
    assert app.operating_state is ApplicationOperatingState.RUNNING

    computer.power_off()

    for i in range(computer.shut_down_duration + 1):
        computer.apply_timestep(timestep=i)

    assert computer.operating_state is NodeOperatingState.OFF
    assert app.operating_state is ApplicationOperatingState.CLOSED

    computer.power_on()

    for i in range(computer.start_up_duration + 1):
        computer.apply_timestep(timestep=i)

    assert computer.operating_state is NodeOperatingState.ON
    assert app.operating_state is ApplicationOperatingState.RUNNING

    computer.start_up_duration = 0
    computer.shut_down_duration = 0

    computer.power_off()
    assert computer.operating_state is NodeOperatingState.OFF
    assert app.operating_state is ApplicationOperatingState.CLOSED

    computer.power_on()
    assert computer.operating_state is NodeOperatingState.ON
    assert app.operating_state is ApplicationOperatingState.RUNNING
