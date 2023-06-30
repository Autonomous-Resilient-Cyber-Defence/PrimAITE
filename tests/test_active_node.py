"""Used to test Active Node functions."""
import pytest

from primaite.common.enums import FileSystemState, HardwareState, SoftwareState
from primaite.nodes.active_node import ActiveNode


@pytest.mark.parametrize(
    "operating_state, expected_state",
    [
        (HardwareState.OFF, SoftwareState.GOOD),
        (HardwareState.ON, SoftwareState.OVERWHELMED),
    ],
)
def test_os_state_change(operating_state, expected_state):
    """
    Test that a node cannot change its Software State.

    When its hardware state is OFF.
    """
    active_node = ActiveNode(
        0,
        "node",
        "COMPUTER",
        "1",
        operating_state,
        "192.168.0.1",
        SoftwareState.GOOD,
        "GOOD",
        1,
    )

    active_node.software_state = SoftwareState.OVERWHELMED

    assert active_node.software_state == expected_state


@pytest.mark.parametrize(
    "operating_state, expected_state",
    [
        (HardwareState.OFF, SoftwareState.GOOD),
        (HardwareState.ON, SoftwareState.OVERWHELMED),
    ],
)
def test_os_state_change_if_not_compromised(operating_state, expected_state):
    """
    Test that a node cannot change its Software State.

    If not compromised) when its hardware state is OFF.
    """
    active_node = ActiveNode(
        0,
        "node",
        "COMPUTER",
        "1",
        operating_state,
        "192.168.0.1",
        SoftwareState.GOOD,
        "GOOD",
        1,
    )

    active_node.set_software_state_if_not_compromised(
        SoftwareState.OVERWHELMED
    )

    assert active_node.software_state == expected_state


@pytest.mark.parametrize(
    "operating_state, expected_state",
    [
        (HardwareState.OFF, FileSystemState.GOOD),
        (HardwareState.ON, FileSystemState.CORRUPT),
    ],
)
def test_file_system_change(operating_state, expected_state):
    """Test that a node cannot change its file system state when its hardware state is ON."""
    active_node = ActiveNode(
        0,
        "node",
        "COMPUTER",
        "1",
        operating_state,
        "192.168.0.1",
        "COMPROMISED",
        FileSystemState.GOOD,
        1,
    )

    active_node.set_file_system_state(FileSystemState.CORRUPT)

    assert active_node.file_system_state_actual == expected_state


@pytest.mark.parametrize(
    "operating_state, expected_state",
    [
        (HardwareState.OFF, FileSystemState.GOOD),
        (HardwareState.ON, FileSystemState.CORRUPT),
    ],
)
def test_file_system_change_if_not_compromised(
    operating_state, expected_state
):
    """
    Test that a node cannot change its file system state.

    If not compromised) when its hardware state is OFF.
    """
    active_node = ActiveNode(
        0,
        "node",
        "COMPUTER",
        "1",
        operating_state,
        "192.168.0.1",
        "GOOD",
        FileSystemState.GOOD,
        1,
    )

    active_node.set_file_system_state_if_not_compromised(
        FileSystemState.CORRUPT
    )

    assert active_node.file_system_state_actual == expected_state
