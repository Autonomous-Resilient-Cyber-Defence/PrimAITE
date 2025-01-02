# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
import os
import shutil
import tempfile
from pathlib import Path

import pkg_resources
import pytest
import yaml

from primaite import PRIMAITE_CONFIG
from primaite.utils.cli.primaite_config_utils import update_primaite_application_config
from tests.integration_tests.cli import cli


@pytest.fixture(autouse=True)
def test_setup():
    """
    Setup this test by using the default primaite app config in package
    """
    global PRIMAITE_CONFIG
    current_config = PRIMAITE_CONFIG.copy()  # store the config before test

    pkg_config_path = Path(pkg_resources.resource_filename("primaite", "setup/_package_data/primaite_config.yaml"))

    with open(pkg_config_path, "r") as file:
        # load from config
        config_dict = yaml.safe_load(file)

    PRIMAITE_CONFIG["developer_mode"] = config_dict["developer_mode"]

    yield

    PRIMAITE_CONFIG["developer_mode"] = current_config["developer_mode"]  # restore config to prevent being yelled at
    update_primaite_application_config(config=PRIMAITE_CONFIG)


def test_dev_mode_enable_disable():
    """Test dev mode enable and disable."""
    # check defaults
    assert PRIMAITE_CONFIG["developer_mode"]["enabled"] is False  # not enabled by default

    result = cli(["dev-mode", "show"])
    assert "Production" in result.output  # should print that it is in Production mode by default

    result = cli(["dev-mode", "enable"])

    assert "Development" in result.output  # should print that it is in Development mode

    assert PRIMAITE_CONFIG["developer_mode"]["enabled"]  # config should reflect that dev mode is enabled

    result = cli(["dev-mode", "show"])
    assert "Development" in result.output  # should print that it is in Development mode

    result = cli(["dev-mode", "disable"])

    assert "Production" in result.output  # should print that it is in Production mode

    assert PRIMAITE_CONFIG["developer_mode"]["enabled"] is False  # config should reflect that dev mode is disabled

    result = cli(["dev-mode", "show"])
    assert "Production" in result.output  # should print that it is in Production mode


def test_dev_mode_config_sys_log_level():
    """Check that the system log level can be changed via CLI."""
    # check defaults
    assert PRIMAITE_CONFIG["developer_mode"]["sys_log_level"] == "DEBUG"  # DEBUG by default

    result = cli(["dev-mode", "config", "-slevel", "WARNING"])

    assert "sys_log_level=WARNING" in result.output  # should print correct value

    # config should reflect that log level is WARNING
    assert PRIMAITE_CONFIG["developer_mode"]["sys_log_level"] == "WARNING"

    result = cli(["dev-mode", "config", "--sys-log-level", "INFO"])

    assert "sys_log_level=INFO" in result.output  # should print correct value

    # config should reflect that log level is INFO
    assert PRIMAITE_CONFIG["developer_mode"]["sys_log_level"] == "INFO"


def test_dev_mode_config_agent_log_level():
    """Check that the agent log level can be changed via CLI."""
    # check defaults
    assert PRIMAITE_CONFIG["developer_mode"]["agent_log_level"] == "DEBUG"  # DEBUG by default

    result = cli(["dev-mode", "config", "-alevel", "WARNING"])

    assert "agent_log_level=WARNING" in result.output  # should print correct value

    # config should reflect that log level is WARNING
    assert PRIMAITE_CONFIG["developer_mode"]["agent_log_level"] == "WARNING"

    result = cli(["dev-mode", "config", "--agent-log-level", "INFO"])

    assert "agent_log_level=INFO" in result.output  # should print correct value

    # config should reflect that log level is INFO
    assert PRIMAITE_CONFIG["developer_mode"]["agent_log_level"] == "INFO"


def test_dev_mode_config_sys_logs_enable_disable():
    """Test that the system logs output can be enabled or disabled."""
    # check defaults
    assert PRIMAITE_CONFIG["developer_mode"]["output_sys_logs"] is False  # False by default

    result = cli(["dev-mode", "config", "--output-sys-logs"])
    assert "output_sys_logs=True" in result.output  # should print correct value

    # config should reflect that output_sys_logs is True
    assert PRIMAITE_CONFIG["developer_mode"]["output_sys_logs"]

    result = cli(["dev-mode", "config", "--no-sys-logs"])
    assert "output_sys_logs=False" in result.output  # should print correct value

    # config should reflect that output_sys_logs is True
    assert PRIMAITE_CONFIG["developer_mode"]["output_sys_logs"] is False

    result = cli(["dev-mode", "config", "-sys"])
    assert "output_sys_logs=True" in result.output  # should print correct value

    # config should reflect that output_sys_logs is True
    assert PRIMAITE_CONFIG["developer_mode"]["output_sys_logs"]

    result = cli(["dev-mode", "config", "-nsys"])
    assert "output_sys_logs=False" in result.output  # should print correct value

    # config should reflect that output_sys_logs is True
    assert PRIMAITE_CONFIG["developer_mode"]["output_sys_logs"] is False


def test_dev_mode_config_agent_logs_enable_disable():
    """Test that the agent logs output can be enabled or disabled."""
    # check defaults
    assert PRIMAITE_CONFIG["developer_mode"]["output_agent_logs"] is False  # False by default

    result = cli(["dev-mode", "config", "--output-agent-logs"])
    assert "output_agent_logs=True" in result.output  # should print correct value

    # config should reflect that output_agent_logs is True
    assert PRIMAITE_CONFIG["developer_mode"]["output_agent_logs"]

    result = cli(["dev-mode", "config", "--no-agent-logs"])
    assert "output_agent_logs=False" in result.output  # should print correct value

    # config should reflect that output_agent_logs is True
    assert PRIMAITE_CONFIG["developer_mode"]["output_agent_logs"] is False

    result = cli(["dev-mode", "config", "-agent"])
    assert "output_agent_logs=True" in result.output  # should print correct value

    # config should reflect that output_agent_logs is True
    assert PRIMAITE_CONFIG["developer_mode"]["output_agent_logs"]

    result = cli(["dev-mode", "config", "-nagent"])
    assert "output_agent_logs=False" in result.output  # should print correct value

    # config should reflect that output_agent_logs is True
    assert PRIMAITE_CONFIG["developer_mode"]["output_agent_logs"] is False


def test_dev_mode_config_pcap_logs_enable_disable():
    """Test that the pcap logs output can be enabled or disabled."""
    # check defaults
    assert PRIMAITE_CONFIG["developer_mode"]["output_pcap_logs"] is False  # False by default

    result = cli(["dev-mode", "config", "--output-pcap-logs"])
    assert "output_pcap_logs=True" in result.output  # should print correct value

    # config should reflect that output_pcap_logs is True
    assert PRIMAITE_CONFIG["developer_mode"]["output_pcap_logs"]

    result = cli(["dev-mode", "config", "--no-pcap-logs"])
    assert "output_pcap_logs=False" in result.output  # should print correct value

    # config should reflect that output_pcap_logs is True
    assert PRIMAITE_CONFIG["developer_mode"]["output_pcap_logs"] is False

    result = cli(["dev-mode", "config", "-pcap"])
    assert "output_pcap_logs=True" in result.output  # should print correct value

    # config should reflect that output_pcap_logs is True
    assert PRIMAITE_CONFIG["developer_mode"]["output_pcap_logs"]

    result = cli(["dev-mode", "config", "-npcap"])
    assert "output_pcap_logs=False" in result.output  # should print correct value

    # config should reflect that output_pcap_logs is True
    assert PRIMAITE_CONFIG["developer_mode"]["output_pcap_logs"] is False


def test_dev_mode_config_output_to_terminal_enable_disable():
    """Test that the output to terminal can be enabled or disabled."""
    # check defaults
    assert PRIMAITE_CONFIG["developer_mode"]["output_to_terminal"] is False  # False by default

    result = cli(["dev-mode", "config", "--output-to-terminal"])
    assert "output_to_terminal=True" in result.output  # should print correct value

    # config should reflect that output_to_terminal is True
    assert PRIMAITE_CONFIG["developer_mode"]["output_to_terminal"]

    result = cli(["dev-mode", "config", "--no-terminal"])
    assert "output_to_terminal=False" in result.output  # should print correct value

    # config should reflect that output_to_terminal is True
    assert PRIMAITE_CONFIG["developer_mode"]["output_to_terminal"] is False

    result = cli(["dev-mode", "config", "-t"])
    assert "output_to_terminal=True" in result.output  # should print correct value

    # config should reflect that output_to_terminal is True
    assert PRIMAITE_CONFIG["developer_mode"]["output_to_terminal"]

    result = cli(["dev-mode", "config", "-nt"])
    assert "output_to_terminal=False" in result.output  # should print correct value

    # config should reflect that output_to_terminal is True
    assert PRIMAITE_CONFIG["developer_mode"]["output_to_terminal"] is False
