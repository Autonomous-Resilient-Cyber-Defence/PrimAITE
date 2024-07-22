# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from unittest.mock import Mock

import pytest

from primaite.game.agent.actions import (
    ActionManager,
    DoNothingAction,
    NodeServiceDisableAction,
    NodeServiceEnableAction,
    NodeServicePauseAction,
    NodeServiceRestartAction,
    NodeServiceResumeAction,
    NodeServiceScanAction,
    NodeServiceStartAction,
    NodeServiceStopAction,
)


def test_do_nothing_action_form_request():
    """Test that the DoNothingAction can form a request and that it is correct."""
    manager = Mock()

    action = DoNothingAction(manager=manager)

    request = action.form_request()

    assert request == ["do_nothing"]


@pytest.mark.parametrize(
    "action_class,              action_verb",
    [
        (NodeServiceScanAction, "scan"),
        (NodeServiceStopAction, "stop"),
        (NodeServiceStartAction, "start"),
        (NodeServicePauseAction, "pause"),
        (NodeServiceResumeAction, "resume"),
        (NodeServiceRestartAction, "restart"),
        (NodeServiceDisableAction, "disable"),
        (NodeServiceEnableAction, "enable"),
    ],
)  # flake8: noqa
@pytest.mark.parametrize(
    "node_name, service_name, expect_to_do_nothing",
    [
        ("pc_1", "chrome", False),
        (None, "chrome", True),
        ("pc_1", None, True),
        (None, None, True),
    ],
)  # flake8: noqa
def test_service_action_form_request(node_name, service_name, expect_to_do_nothing, action_class, action_verb):
    """Test that the ServiceScanAction can form a request and that it is correct."""
    manager: ActionManager = Mock()
    manager.get_node_name_by_idx.return_value = node_name
    manager.get_service_name_by_idx.return_value = service_name

    action = action_class(manager=manager, num_nodes=1, num_services=1)

    request = action.form_request(node_id=0, service_id=0)

    if expect_to_do_nothing:
        assert request == ["do_nothing"]
    else:
        assert request == ["network", "node", node_name, "service", service_name, action_verb]


@pytest.mark.parametrize(
    "node_name, service_name, expect_to_do_nothing",
    [
        ("pc_1", "chrome", False),
        (None, "chrome", True),
        ("pc_1", None, True),
        (None, None, True),
    ],
)  # flake8: noqa
def test_service_scan_form_request(node_name, service_name, expect_to_do_nothing):
    """Test that the ServiceScanAction can form a request and that it is correct."""
    manager: ActionManager = Mock()
    manager.get_node_name_by_idx.return_value = node_name
    manager.get_service_name_by_idx.return_value = service_name

    action = NodeServiceScanAction(manager=manager, num_nodes=1, num_services=1)

    request = action.form_request(node_id=0, service_id=0)

    if expect_to_do_nothing:
        assert request == ["do_nothing"]
    else:
        assert request == ["network", "node", node_name, "service", service_name, "scan"]
