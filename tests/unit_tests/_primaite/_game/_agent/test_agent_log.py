# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from uuid import uuid4

import pytest

from primaite import PRIMAITE_CONFIG
from primaite.game.agent.agent_log import AgentLog
from primaite.simulator import LogLevel, SIM_OUTPUT


@pytest.fixture(autouse=True)
def override_dev_mode_temporarily():
    """Temporarily turn off dev mode for this test."""
    primaite_dev_mode = PRIMAITE_CONFIG["developer_mode"]["enabled"]
    PRIMAITE_CONFIG["developer_mode"]["enabled"] = False
    yield  # run tests
    PRIMAITE_CONFIG["developer_mode"]["enabled"] = primaite_dev_mode


@pytest.fixture(scope="function")
def agentlog() -> AgentLog:
    return AgentLog(agent_name="test_agent")


def test_debug_agent_log_level(agentlog, capsys):
    """Test that the debug log level logs debug agent logs and above."""
    SIM_OUTPUT.agent_log_level = LogLevel.DEBUG
    SIM_OUTPUT.write_agent_log_to_terminal = True

    test_string = str(uuid4())

    agentlog.debug(msg=test_string)
    agentlog.info(msg=test_string)
    agentlog.warning(msg=test_string)
    agentlog.error(msg=test_string)
    agentlog.critical(msg=test_string)

    captured = "".join(capsys.readouterr())

    assert test_string in captured
    assert "DEBUG" in captured
    assert "INFO" in captured
    assert "WARNING" in captured
    assert "ERROR" in captured
    assert "CRITICAL" in captured


def test_info_agent_log_level(agentlog, capsys):
    """Test that the debug log level logs debug agent logs and above."""
    SIM_OUTPUT.agent_log_level = LogLevel.INFO
    SIM_OUTPUT.write_agent_log_to_terminal = True

    test_string = str(uuid4())

    agentlog.debug(msg=test_string)
    agentlog.info(msg=test_string)
    agentlog.warning(msg=test_string)
    agentlog.error(msg=test_string)
    agentlog.critical(msg=test_string)

    captured = "".join(capsys.readouterr())

    assert test_string in captured
    assert "DEBUG" not in captured
    assert "INFO" in captured
    assert "WARNING" in captured
    assert "ERROR" in captured
    assert "CRITICAL" in captured


def test_warning_agent_log_level(agentlog, capsys):
    """Test that the debug log level logs debug agent logs and above."""
    SIM_OUTPUT.agent_log_level = LogLevel.WARNING
    SIM_OUTPUT.write_agent_log_to_terminal = True

    test_string = str(uuid4())

    agentlog.debug(msg=test_string)
    agentlog.info(msg=test_string)
    agentlog.warning(msg=test_string)
    agentlog.error(msg=test_string)
    agentlog.critical(msg=test_string)

    captured = "".join(capsys.readouterr())

    assert test_string in captured
    assert "DEBUG" not in captured
    assert "INFO" not in captured
    assert "WARNING" in captured
    assert "ERROR" in captured
    assert "CRITICAL" in captured


def test_error_agent_log_level(agentlog, capsys):
    """Test that the debug log level logs debug agent logs and above."""
    SIM_OUTPUT.agent_log_level = LogLevel.ERROR
    SIM_OUTPUT.write_agent_log_to_terminal = True

    test_string = str(uuid4())

    agentlog.debug(msg=test_string)
    agentlog.info(msg=test_string)
    agentlog.warning(msg=test_string)
    agentlog.error(msg=test_string)
    agentlog.critical(msg=test_string)

    captured = "".join(capsys.readouterr())

    assert test_string in captured
    assert "DEBUG" not in captured
    assert "INFO" not in captured
    assert "WARNING" not in captured
    assert "ERROR" in captured
    assert "CRITICAL" in captured


def test_critical_agent_log_level(agentlog, capsys):
    """Test that the debug log level logs debug agent logs and above."""
    SIM_OUTPUT.agent_log_level = LogLevel.CRITICAL
    SIM_OUTPUT.write_agent_log_to_terminal = True

    test_string = str(uuid4())

    agentlog.debug(msg=test_string)
    agentlog.info(msg=test_string)
    agentlog.warning(msg=test_string)
    agentlog.error(msg=test_string)
    agentlog.critical(msg=test_string)

    captured = "".join(capsys.readouterr())

    assert test_string in captured
    assert "DEBUG" not in captured
    assert "INFO" not in captured
    assert "WARNING" not in captured
    assert "ERROR" not in captured
    assert "CRITICAL" in captured
