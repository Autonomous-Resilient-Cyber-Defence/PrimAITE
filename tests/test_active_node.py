"""Used to test Active Node functions."""
import pytest

from primaite.common.enums import FILE_SYSTEM_STATE, HARDWARE_STATE, SOFTWARE_STATE
from primaite.nodes.active_node import ActiveNode


@pytest.mark.parametrize(
    "operating_state, expected_state",
    [
        (HARDWARE_STATE.OFF, SOFTWARE_STATE.GOOD),
        (HARDWARE_STATE.ON, SOFTWARE_STATE.OVERWHELMED),
    ],
)
def test_os_state_change(operating_state, expected_state):
    """
    Test that a node cannot change its operating system state.

    When its operating state is OFF.
    """
    active_node = ActiveNode(
        0,
        "node",
        "COMPUTER",
        "1",
        operating_state,
        "192.168.0.1",
        SOFTWARE_STATE.GOOD,
        "GOOD",
        1,
    )

    active_node.set_os_state(SOFTWARE_STATE.OVERWHELMED)

    assert active_node.get_os_state() == expected_state


@pytest.mark.parametrize(
    "operating_state, expected_state",
    [
        (HARDWARE_STATE.OFF, SOFTWARE_STATE.GOOD),
        (HARDWARE_STATE.ON, SOFTWARE_STATE.OVERWHELMED),
    ],
)
def test_os_state_change_if_not_compromised(operating_state, expected_state):
    """
    Test that a node cannot change its operating system state.

    If not compromised) when its operating state is OFF.
    """
    active_node = ActiveNode(
        0,
        "node",
        "COMPUTER",
        "1",
        operating_state,
        "192.168.0.1",
        SOFTWARE_STATE.GOOD,
        "GOOD",
        1,
    )

    active_node.set_os_state_if_not_compromised(SOFTWARE_STATE.OVERWHELMED)

    assert active_node.get_os_state() == expected_state


@pytest.mark.parametrize(
    "operating_state, expected_state",
    [
        (HARDWARE_STATE.OFF, FILE_SYSTEM_STATE.GOOD),
        (HARDWARE_STATE.ON, FILE_SYSTEM_STATE.CORRUPT),
    ],
)
def test_file_system_change(operating_state, expected_state):
    """Test that a node cannot change its file system state when its operating state is ON."""
    active_node = ActiveNode(
        0,
        "node",
        "COMPUTER",
        "1",
        operating_state,
        "192.168.0.1",
        "COMPROMISED",
        FILE_SYSTEM_STATE.GOOD,
        1,
    )

    active_node.set_file_system_state(FILE_SYSTEM_STATE.CORRUPT)

    assert active_node.get_file_system_state_actual() == expected_state


@pytest.mark.parametrize(
    "operating_state, expected_state",
    [
        (HARDWARE_STATE.OFF, FILE_SYSTEM_STATE.GOOD),
        (HARDWARE_STATE.ON, FILE_SYSTEM_STATE.CORRUPT),
    ],
)
def test_file_system_change_if_not_compromised(operating_state, expected_state):
    """
    Test that a node cannot change its file system state.

    If not compromised) when its operating state is OFF.
    """
    active_node = ActiveNode(
        0,
        "node",
        "COMPUTER",
        "1",
        operating_state,
        "192.168.0.1",
        "GOOD",
        FILE_SYSTEM_STATE.GOOD,
        1,
    )

    active_node.set_file_system_state_if_not_compromised(FILE_SYSTEM_STATE.CORRUPT)

    assert active_node.get_file_system_state_actual() == expected_state
