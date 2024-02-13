"""Warning: SIM_OUTPUT is a mutable global variable for the simulation output directory."""
from datetime import datetime
from pathlib import Path

from primaite import _PRIMAITE_ROOT

__all__ = ["SIM_OUTPUT"]


class _SimOutput:
    def __init__(self):
        self._path: Path = (
            _PRIMAITE_ROOT.parent.parent / "simulation_output" / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        )
        self.save_pcap_logs: bool = True
        self.save_sys_logs: bool = True

    @property
    def path(self) -> Path:
        return self._path

    @path.setter
    def path(self, new_path: Path) -> None:
        self._path = new_path
        self._path.mkdir(exist_ok=True, parents=True)


SIM_OUTPUT = _SimOutput()
