"""Warning: SIM_OUTPUT is a mutable global variable for the simulation output directory."""
from datetime import datetime
from enum import IntEnum
from pathlib import Path

from primaite import _PRIMAITE_ROOT

__all__ = ["SIM_OUTPUT"]

from primaite.utils.cli.primaite_config_utils import get_primaite_config_dict, is_dev_mode


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
    _default_path = _PRIMAITE_ROOT.parent.parent / "simulation_output" / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    def __init__(self):
        self._path: Path = self._default_path
        self.save_pcap_logs: bool = False
        self.save_sys_logs: bool = False
        self.write_sys_log_to_terminal: bool = False
        self.sys_log_level: LogLevel = LogLevel.WARNING  # default log level is at WARNING

        if is_dev_mode():
            # if dev mode, override with the values configured via the primaite dev-mode command
            dev_config = get_primaite_config_dict().get("developer_mode")
            self.save_pcap_logs = dev_config["output_pcap_logs"]
            self.save_sys_logs = dev_config["output_sys_logs"]
            self.write_sys_log_to_terminal = dev_config["output_to_terminal"]

    @property
    def path(self) -> Path:
        if not is_dev_mode():
            return self._path
        if is_dev_mode():
            dev_config = get_primaite_config_dict().get("developer_mode")
            return Path(dev_config["output_dir"]) if dev_config["output_dir"] else self._default_path

    @path.setter
    def path(self, new_path: Path) -> None:
        self._path = new_path
        self._path.mkdir(exist_ok=True, parents=True)


SIM_OUTPUT = _SimOutput()
