"""Used to test Active Node functions."""
import pytest

from primaite.common.enums import FileSystemState, HardwareState, SoftwareState, NodeType, Priority
from primaite.common.service import Service
from primaite.config.training_config import TrainingConfig
from primaite.nodes.active_node import ActiveNode
from primaite.nodes.service_node import ServiceNode


@pytest.mark.parametrize(
    "starting_operating_state, expected_operating_state",
    [
        (HardwareState.RESETTING, HardwareState.ON)
    ],
)
def test_node_resets_correctly(starting_operating_state, expected_operating_state):
    """
    Tests that a node resets correctly.
    """
    active_node = ActiveNode(
        node_id = "0",
        name = "node",
        node_type = NodeType.COMPUTER,
        priority = Priority.P1,
        hardware_state = starting_operating_state,
        ip_address = "192.168.0.1",
        software_state = SoftwareState.COMPROMISED,
        file_system_state = FileSystemState.CORRUPT,
        config_values=TrainingConfig()
    )

    for x in range(5):
        active_node.update_resetting_status()

    assert active_node.software_state == SoftwareState.GOOD
    assert active_node.file_system_state_actual == FileSystemState.GOOD
    assert active_node.hardware_state == expected_operating_state

@pytest.mark.parametrize(
    "operating_state, expected_operating_state",
    [
        (HardwareState.BOOTING, HardwareState.ON)
    ],
)
def test_node_boots_correctly(operating_state, expected_operating_state):
    """
    Tests that a node boots correctly.
    """
    service_node = ServiceNode(
        node_id = 0,
        name = "node",
        node_type = "COMPUTER",
        priority = "1",
        hardware_state = operating_state,
        ip_address = "192.168.0.1",
        software_state = SoftwareState.GOOD,
        file_system_state = "GOOD",
        config_values = 1,
    )
    service_attributes = Service(
        name = "node",
        port = "80",
        software_state = SoftwareState.COMPROMISED
    )
    service_node.add_service(
        service_attributes
    )

    for x in range(5):
        service_node.update_booting_status()

    assert service_attributes.software_state == SoftwareState.GOOD
    assert service_node.hardware_state == expected_operating_state

@pytest.mark.parametrize(
    "operating_state, expected_operating_state",
    [
        (HardwareState.SHUTTING_DOWN, HardwareState.OFF)
    ],
)
def test_node_shutdown_correctly(operating_state, expected_operating_state):
    """
    Tests that a node shutdown correctly.
    """
    active_node = ActiveNode(
        node_id = 0,
        name = "node",
        node_type = "COMPUTER",
        priority = "1",
        hardware_state = operating_state,
        ip_address = "192.168.0.1",
        software_state = SoftwareState.GOOD,
        file_system_state = "GOOD",
        config_values = 1,
    )

    for x in range(5):
        active_node.update_shutdown_status()

    assert active_node.hardware_state == expected_operating_state


