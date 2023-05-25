"""Used to test Service Node functions."""
import pytest

from primaite.common.enums import HARDWARE_STATE, SOFTWARE_STATE
from primaite.common.service import Service
from primaite.nodes.service_node import ServiceNode


@pytest.mark.parametrize(
    "operating_state, expected_state",
    [
        (HARDWARE_STATE.OFF, SOFTWARE_STATE.GOOD),
        (HARDWARE_STATE.ON, SOFTWARE_STATE.OVERWHELMED),
    ],
)
def test_service_state_change(operating_state, expected_state):
    """
    Test that a node cannot change the state of a running service.

    When its operating state is OFF.
    """
    service_node = ServiceNode(
        0,
        "node",
        "COMPUTER",
        "1",
        operating_state,
        "192.168.0.1",
        "COMPROMISED",
        "RESTORING",
        1,
    )
    service = Service("TCP", 80, SOFTWARE_STATE.GOOD)
    service_node.add_service(service)

    service_node.set_service_state("TCP", SOFTWARE_STATE.OVERWHELMED)

    assert service_node.get_service_state("TCP") == expected_state


@pytest.mark.parametrize(
    "operating_state, expected_state",
    [
        (HARDWARE_STATE.OFF, SOFTWARE_STATE.GOOD),
        (HARDWARE_STATE.ON, SOFTWARE_STATE.OVERWHELMED),
    ],
)
def test_service_state_change_if_not_comprised(operating_state, expected_state):
    """
    Test that a node cannot change the state of a running service.

    If not compromised when its operating state is ON.
    """
    service_node = ServiceNode(
        0,
        "node",
        "COMPUTER",
        "1",
        operating_state,
        "192.168.0.1",
        "GOOD",
        "RESTORING",
        1,
    )
    service = Service("TCP", 80, SOFTWARE_STATE.GOOD)
    service_node.add_service(service)

    service_node.set_service_state_if_not_compromised("TCP", SOFTWARE_STATE.OVERWHELMED)

    assert service_node.get_service_state("TCP") == expected_state
