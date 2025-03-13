# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
"""The PrimAITE simulation layer."""
from datetime import datetime
from enum import IntEnum
from pathlib import Path

from primaite import _PRIMAITE_ROOT, PRIMAITE_CONFIG, PRIMAITE_PATHS

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
        self.date_str = datetime.now().strftime("%Y-%m-%d")
        self.time_str = datetime.now().strftime("%H-%M-%S")

        path = PRIMAITE_PATHS.user_sessions_path / self.date_str / self.time_str

        self._path = path
        self._agent_behaviour_path = path
        self._save_pcap_logs: bool = False
        self._save_sys_logs: bool = False
        self._save_agent_logs: bool = False
        self._write_sys_log_to_terminal: bool = False
        self._write_agent_log_to_terminal: bool = False
        self._sys_log_level: LogLevel = LogLevel.WARNING  # default log level is at WARNING
        self._agent_log_level: LogLevel = LogLevel.WARNING

    @property
    def path(self) -> Path:
        if is_dev_mode():
            # if dev mode is enabled, if output dir is not set, print to primaite repo root
            path: Path = _PRIMAITE_ROOT.parent.parent / "sessions" / self.date_str / self.time_str / "simulation_output"
            # otherwise print to output dir
            if PRIMAITE_CONFIG["developer_mode"]["output_dir"]:
                path: Path = (
                    Path(PRIMAITE_CONFIG["developer_mode"]["output_dir"])
                    / "sessions"
                    / self.date_str
                    / self.time_str
                    / "simulation_output"
                )
            self._path = path
        return self._path

    @path.setter
    def path(self, new_path: Path) -> None:
        self._path = new_path
        self._path.mkdir(exist_ok=True, parents=True)

    @property
    def agent_behaviour_path(self) -> Path:
        if is_dev_mode():
            # if dev mode is enabled, if output dir is not set, print to primaite repo root
            path: Path = _PRIMAITE_ROOT.parent.parent / "sessions" / self.date_str / self.time_str / "agent_behaviour"
            # otherwise print to output dir
            if PRIMAITE_CONFIG["developer_mode"]["output_dir"]:
                path: Path = (
                    Path(PRIMAITE_CONFIG["developer_mode"]["output_dir"])
                    / "sessions"
                    / self.date_str
                    / self.time_str
                    / "agent_behaviour"
                )
            self._agent_behaviour_path = path
        return self._agent_behaviour_path

    @agent_behaviour_path.setter
    def agent_behaviour_path(self, new_path: Path) -> None:
        self._agent_behaviour_path = new_path
        self._agent_behaviour_path.mkdir(exist_ok=True, parents=True)

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
    def save_agent_logs(self) -> bool:
        if is_dev_mode():
            return PRIMAITE_CONFIG.get("developer_mode").get("output_agent_logs")
        return self._save_agent_logs

    @save_agent_logs.setter
    def save_agent_logs(self, save_agent_logs: bool) -> None:
        self._save_agent_logs = save_agent_logs

    @property
    def write_sys_log_to_terminal(self) -> bool:
        if is_dev_mode():
            return PRIMAITE_CONFIG.get("developer_mode").get("output_to_terminal")
        return self._write_sys_log_to_terminal

    @write_sys_log_to_terminal.setter
    def write_sys_log_to_terminal(self, write_sys_log_to_terminal: bool) -> None:
        self._write_sys_log_to_terminal = write_sys_log_to_terminal

    # Should this be separate from sys_log?
    @property
    def write_agent_log_to_terminal(self) -> bool:
        if is_dev_mode():
            return PRIMAITE_CONFIG.get("developer_mode").get("output_to_terminal")
        return self._write_agent_log_to_terminal

    @write_agent_log_to_terminal.setter
    def write_agent_log_to_terminal(self, write_agent_log_to_terminal: bool) -> None:
        self._write_agent_log_to_terminal = write_agent_log_to_terminal

    @property
    def sys_log_level(self) -> LogLevel:
        if is_dev_mode():
            return LogLevel[PRIMAITE_CONFIG.get("developer_mode").get("sys_log_level")]
        return self._sys_log_level

    @sys_log_level.setter
    def sys_log_level(self, sys_log_level: LogLevel) -> None:
        self._sys_log_level = sys_log_level

    @property
    def agent_log_level(self) -> LogLevel:
        if is_dev_mode():
            return LogLevel[PRIMAITE_CONFIG.get("developer_mode").get("agent_log_level")]
        return self._agent_log_level

    @agent_log_level.setter
    def agent_log_level(self, agent_log_level: LogLevel) -> None:
        self._agent_log_level = agent_log_level


SIM_OUTPUT = _SimOutput()
