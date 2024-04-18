"""Warning: SIM_OUTPUT is a mutable global variable for the simulation output directory."""
from datetime import datetime
from enum import IntEnum
from pathlib import Path

from primaite import _PRIMAITE_ROOT

__all__ = ["SIM_OUTPUT"]


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
        self.save_pcap_logs: bool = False
        self.save_sys_logs: bool = False
        self.write_sys_log_to_terminal: bool = False
        self.sys_log_level: LogLevel = LogLevel.INFO  # default log level is at INFO

    @property
    def path(self) -> Path:
        return self._path

    @path.setter
    def path(self, new_path: Path) -> None:
        self._path = new_path
        self._path.mkdir(exist_ok=True, parents=True)


SIM_OUTPUT = _SimOutput()
