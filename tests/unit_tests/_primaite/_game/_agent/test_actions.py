# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from primaite.game.agent.actions import ActionManager
from primaite.game.agent.actions.manager import DoNothingAction
from primaite.game.agent.actions.service import (
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
    """Test that the do_nothingAction can form a request and that it is correct."""
    request = DoNothingAction.form_request(DoNothingAction.ConfigSchema())
    assert request == ["do-nothing"]


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
    "node_name, service_name, expect_failure",
    [
        ("pc_1", "chrome", False),
        (None, "chrome", True),
        ("pc_1", None, True),
        (None, None, True),
    ],
)  # flake8: noqa
def test_service_action_form_request(node_name, service_name, expect_failure, action_class, action_verb):
    """Test that the ServiceScanAction can form a request and that it is correct."""
    if expect_failure:
        with pytest.raises(ValidationError):
            request = action_class.form_request(
                config=action_class.ConfigSchema(node_name=node_name, service_name=service_name)
            )
    else:
        request = action_class.form_request(
            config=action_class.ConfigSchema(node_name=node_name, service_name=service_name)
        )
        assert request == ["network", "node", node_name, "service", service_name, action_verb]
