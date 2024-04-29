from uuid import uuid4

import pytest

from primaite.simulator import LogLevel, SIM_OUTPUT
from primaite.simulator.system.core.sys_log import SysLog


@pytest.fixture(scope="function")
def syslog() -> SysLog:
    return SysLog(hostname="test")


def test_debug_sys_log_level(syslog, capsys):
    """Test that the debug log level logs debug syslogs and above."""
    SIM_OUTPUT.sys_log_level = LogLevel.DEBUG
    SIM_OUTPUT.write_sys_log_to_terminal = True

    test_string = str(uuid4())

    syslog.debug(test_string)
    syslog.info(test_string)
    syslog.warning(test_string)
    syslog.error(test_string)
    syslog.critical(test_string)

    captured = "".join(capsys.readouterr())

    assert test_string in captured
    assert "DEBUG" in captured
    assert "INFO" in captured
    assert "WARNING" in captured
    assert "ERROR" in captured
    assert "CRITICAL" in captured


def test_info_sys_log_level(syslog, capsys):
    """Test that the debug log level logs debug syslogs and above."""
    SIM_OUTPUT.sys_log_level = LogLevel.INFO
    SIM_OUTPUT.write_sys_log_to_terminal = True

    test_string = str(uuid4())

    syslog.debug(test_string)
    syslog.info(test_string)
    syslog.warning(test_string)
    syslog.error(test_string)
    syslog.critical(test_string)

    captured = "".join(capsys.readouterr())

    assert test_string in captured
    assert "DEBUG" not in captured
    assert "INFO" in captured
    assert "WARNING" in captured
    assert "ERROR" in captured
    assert "CRITICAL" in captured


def test_warning_sys_log_level(syslog, capsys):
    """Test that the debug log level logs debug syslogs and above."""
    SIM_OUTPUT.sys_log_level = LogLevel.WARNING
    SIM_OUTPUT.write_sys_log_to_terminal = True

    test_string = str(uuid4())

    syslog.debug(test_string)
    syslog.info(test_string)
    syslog.warning(test_string)
    syslog.error(test_string)
    syslog.critical(test_string)

    captured = "".join(capsys.readouterr())

    assert test_string in captured
    assert "DEBUG" not in captured
    assert "INFO" not in captured
    assert "WARNING" in captured
    assert "ERROR" in captured
    assert "CRITICAL" in captured


def test_error_sys_log_level(syslog, capsys):
    """Test that the debug log level logs debug syslogs and above."""
    SIM_OUTPUT.sys_log_level = LogLevel.ERROR
    SIM_OUTPUT.write_sys_log_to_terminal = True

    test_string = str(uuid4())

    syslog.debug(test_string)
    syslog.info(test_string)
    syslog.warning(test_string)
    syslog.error(test_string)
    syslog.critical(test_string)

    captured = "".join(capsys.readouterr())

    assert test_string in captured
    assert "DEBUG" not in captured
    assert "INFO" not in captured
    assert "WARNING" not in captured
    assert "ERROR" in captured
    assert "CRITICAL" in captured


def test_critical_sys_log_level(syslog, capsys):
    """Test that the debug log level logs debug syslogs and above."""
    SIM_OUTPUT.sys_log_level = LogLevel.CRITICAL
    SIM_OUTPUT.write_sys_log_to_terminal = True

    test_string = str(uuid4())

    syslog.debug(test_string)
    syslog.info(test_string)
    syslog.warning(test_string)
    syslog.error(test_string)
    syslog.critical(test_string)

    captured = "".join(capsys.readouterr())

    assert test_string in captured
    assert "DEBUG" not in captured
    assert "INFO" not in captured
    assert "WARNING" not in captured
    assert "ERROR" not in captured
    assert "CRITICAL" in captured
