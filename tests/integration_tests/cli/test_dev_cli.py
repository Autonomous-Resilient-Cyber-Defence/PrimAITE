import os
import shutil
import tempfile
from pathlib import Path

import pkg_resources
import pytest
import yaml
from _pytest.monkeypatch import MonkeyPatch

import primaite
from tests.integration_tests.cli import cli


@pytest.fixture(autouse=True)
def test_setup():
    """
    Setup this test by using the default primaite app config in package
    """
    current_config = primaite.PRIMAITE_CONFIG  # store the config before test
    original_config_path = primaite.PRIMAITE_PATHS.app_config_file_path  # keep track of app config before test

    temp_dir = tempfile.gettempdir()
    temp_config = Path(temp_dir) / "primaite_config.yaml"
    pkg_config_path = Path(pkg_resources.resource_filename("primaite", "setup/_package_data/primaite_config.yaml"))
    shutil.copyfile(pkg_config_path, temp_config)  # copy the default primaite config to temp directory
    primaite.PRIMAITE_PATHS.app_config_file_path = temp_config  # use the copy for the test

    with open(pkg_config_path, "r") as file:
        # load from config
        config_dict = yaml.safe_load(file)

    primaite.PRIMAITE_CONFIG = config_dict
    assert primaite.PRIMAITE_CONFIG == config_dict

    yield

    os.remove(temp_config)  # clean up temp file
    primaite.PRIMAITE_CONFIG = current_config  # restore config to prevent being yelled at
    assert primaite.PRIMAITE_CONFIG == current_config
    primaite.PRIMAITE_PATHS.app_config_file_path = original_config_path


@pytest.mark.skip(reason="borked")
def test_dev_mode_enable_disable():
    """Test dev mode enable and disable."""
    # check defaults
    assert primaite.PRIMAITE_CONFIG["developer_mode"]["enabled"] is False  # not enabled by default

    result = cli(["dev-mode", "show"])
    assert "Production" in result.output  # should print that it is in Production mode by default

    result = cli(["dev-mode", "enable"])

    assert "Development" in result.output  # should print that it is in Development mode

    assert primaite.PRIMAITE_CONFIG["developer_mode"]["enabled"]  # config should reflect that dev mode is enabled

    result = cli(["dev-mode", "show"])
    assert "Development" in result.output  # should print that it is in Development mode

    result = cli(["dev-mode", "disable"])

    assert "Production" in result.output  # should print that it is in Production mode

    assert (
        primaite.PRIMAITE_CONFIG["developer_mode"]["enabled"] is False
    )  # config should reflect that dev mode is disabled

    result = cli(["dev-mode", "show"])
    assert "Production" in result.output  # should print that it is in Production mode


@pytest.mark.skip(reason="borked")
def test_dev_mode_config_sys_log_level():
    """Check that the system log level can be changed via CLI."""
    # check defaults
    assert primaite.PRIMAITE_CONFIG["developer_mode"]["sys_log_level"] == "DEBUG"  # DEBUG by default

    result = cli(["dev-mode", "config", "-level", "WARNING"])

    assert "sys_log_level=WARNING" in result.output  # should print correct value

    # config should reflect that log level is WARNING
    assert primaite.PRIMAITE_CONFIG["developer_mode"]["sys_log_level"] == "WARNING"

    result = cli(["dev-mode", "config", "--sys-log-level", "INFO"])

    assert "sys_log_level=INFO" in result.output  # should print correct value

    # config should reflect that log level is WARNING
    assert primaite.PRIMAITE_CONFIG["developer_mode"]["sys_log_level"] == "INFO"


@pytest.mark.skip(reason="borked")
def test_dev_mode_config_sys_logs_enable_disable():
    """Test that the system logs output can be enabled or disabled."""
    # check defaults
    assert primaite.PRIMAITE_CONFIG["developer_mode"]["output_sys_logs"] is False  # False by default

    result = cli(["dev-mode", "config", "--output-sys-logs"])
    assert "output_sys_logs=True" in result.output  # should print correct value

    # config should reflect that output_sys_logs is True
    assert primaite.PRIMAITE_CONFIG["developer_mode"]["output_sys_logs"]

    result = cli(["dev-mode", "config", "--no-sys-logs"])
    assert "output_sys_logs=False" in result.output  # should print correct value

    # config should reflect that output_sys_logs is True
    assert primaite.PRIMAITE_CONFIG["developer_mode"]["output_sys_logs"] is False

    result = cli(["dev-mode", "config", "-sys"])
    assert "output_sys_logs=True" in result.output  # should print correct value

    # config should reflect that output_sys_logs is True
    assert primaite.PRIMAITE_CONFIG["developer_mode"]["output_sys_logs"]

    result = cli(["dev-mode", "config", "-nsys"])
    assert "output_sys_logs=False" in result.output  # should print correct value

    # config should reflect that output_sys_logs is True
    assert primaite.PRIMAITE_CONFIG["developer_mode"]["output_sys_logs"] is False


@pytest.mark.skip(reason="borked")
def test_dev_mode_config_pcap_logs_enable_disable():
    """Test that the pcap logs output can be enabled or disabled."""
    # check defaults
    assert primaite.PRIMAITE_CONFIG["developer_mode"]["output_pcap_logs"] is False  # False by default

    result = cli(["dev-mode", "config", "--output-pcap-logs"])
    assert "output_pcap_logs=True" in result.output  # should print correct value

    # config should reflect that output_pcap_logs is True
    assert primaite.PRIMAITE_CONFIG["developer_mode"]["output_pcap_logs"]

    result = cli(["dev-mode", "config", "--no-pcap-logs"])
    assert "output_pcap_logs=False" in result.output  # should print correct value

    # config should reflect that output_pcap_logs is True
    assert primaite.PRIMAITE_CONFIG["developer_mode"]["output_pcap_logs"] is False

    result = cli(["dev-mode", "config", "-pcap"])
    assert "output_pcap_logs=True" in result.output  # should print correct value

    # config should reflect that output_pcap_logs is True
    assert primaite.PRIMAITE_CONFIG["developer_mode"]["output_pcap_logs"]

    result = cli(["dev-mode", "config", "-npcap"])
    assert "output_pcap_logs=False" in result.output  # should print correct value

    # config should reflect that output_pcap_logs is True
    assert primaite.PRIMAITE_CONFIG["developer_mode"]["output_pcap_logs"] is False


@pytest.mark.skip(reason="borked")
def test_dev_mode_config_output_to_terminal_enable_disable():
    """Test that the output to terminal can be enabled or disabled."""
    # check defaults
    assert primaite.PRIMAITE_CONFIG["developer_mode"]["output_to_terminal"] is False  # False by default

    result = cli(["dev-mode", "config", "--output-to-terminal"])
    assert "output_to_terminal=True" in result.output  # should print correct value

    # config should reflect that output_to_terminal is True
    assert primaite.PRIMAITE_CONFIG["developer_mode"]["output_to_terminal"]

    result = cli(["dev-mode", "config", "--no-terminal"])
    assert "output_to_terminal=False" in result.output  # should print correct value

    # config should reflect that output_to_terminal is True
    assert primaite.PRIMAITE_CONFIG["developer_mode"]["output_to_terminal"] is False

    result = cli(["dev-mode", "config", "-t"])
    assert "output_to_terminal=True" in result.output  # should print correct value

    # config should reflect that output_to_terminal is True
    assert primaite.PRIMAITE_CONFIG["developer_mode"]["output_to_terminal"]

    result = cli(["dev-mode", "config", "-nt"])
    assert "output_to_terminal=False" in result.output  # should print correct value

    # config should reflect that output_to_terminal is True
    assert primaite.PRIMAITE_CONFIG["developer_mode"]["output_to_terminal"] is False
