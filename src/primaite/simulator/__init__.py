"""Warning: SIM_OUTPUT is a mutable global variable for the simulation output directory."""
from datetime import datetime
from enum import IntEnum
from pathlib import Path

from primaite import _PRIMAITE_ROOT, PRIMAITE_CONFIG

__all__ = ["SIM_OUTPUT"]

from primaite.utils.cli.primaite_config_utils import is_dev_mode


class LogLevel(IntEnum):
    """Enum containing all the available log levels for PrimAITE simulation output."""

    DEBUG = 10
    """Debug items will be output to terminal or log file."""
    INFO = 20
    """Info items will be output to terminal or log file."""
    WARNING = 30
    """Warnings will be output to terminal or log file."""
    ERROR = 40
    """Errors will be output to terminal or log file."""
    CRITICAL = 50
    """Critical errors will be output to terminal or log file."""


class _SimOutput:
    def __init__(self):
        self._path: Path = (
            _PRIMAITE_ROOT.parent.parent / "simulation_output" / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        )
        self._save_pcap_logs: bool = False
        self._save_sys_logs: bool = False
        self._write_sys_log_to_terminal: bool = False
        self._sys_log_level: LogLevel = LogLevel.WARNING  # default log level is at WARNING

    @property
    def path(self) -> Path:
        return self._path

    @path.setter
    def path(self, new_path: Path) -> None:
        self._path = new_path
        self._path.mkdir(exist_ok=True, parents=True)

    @property
    def save_pcap_logs(self) -> bool:
        if is_dev_mode():
            return PRIMAITE_CONFIG.get("developer_mode").get("output_pcap_logs")
        return self._save_pcap_logs

    @save_pcap_logs.setter
    def save_pcap_logs(self, save_pcap_logs: bool) -> None:
        self._save_pcap_logs = save_pcap_logs

    @property
    def save_sys_logs(self) -> bool:
        if is_dev_mode():
            return PRIMAITE_CONFIG.get("developer_mode").get("output_sys_logs")
        return self._save_sys_logs

    @save_sys_logs.setter
    def save_sys_logs(self, save_sys_logs: bool) -> None:
        self._save_sys_logs = save_sys_logs

    @property
    def write_sys_log_to_terminal(self) -> bool:
        if is_dev_mode():
            return PRIMAITE_CONFIG.get("developer_mode").get("output_to_terminal")
        return self._write_sys_log_to_terminal

    @write_sys_log_to_terminal.setter
    def write_sys_log_to_terminal(self, write_sys_log_to_terminal: bool) -> None:
        self._write_sys_log_to_terminal = write_sys_log_to_terminal

    @property
    def sys_log_level(self) -> LogLevel:
        if is_dev_mode():
            return LogLevel[PRIMAITE_CONFIG.get("developer_mode").get("sys_log_level")]
        return self._sys_log_level

    @sys_log_level.setter
    def sys_log_level(self, sys_log_level: LogLevel) -> None:
        self._sys_log_level = sys_log_level


SIM_OUTPUT = _SimOutput()
