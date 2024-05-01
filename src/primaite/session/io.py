import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from primaite import _PRIMAITE_ROOT, getLogger, PRIMAITE_PATHS
from primaite.simulator import LogLevel, SIM_OUTPUT
from primaite.utils.cli.primaite_config_utils import is_dev_mode

_LOGGER = getLogger(__name__)


class PrimaiteIO:
    """
    Class for managing session IO.

    Currently it's handling path generation, but could expand to handle loading, transaction, and so on.
    """

    class Settings(BaseModel):
        """Config schema for PrimaiteIO object."""

        model_config = ConfigDict(extra="forbid")

        save_logs: bool = True
        """Whether to save logs"""
        save_agent_actions: bool = True
        """Whether to save a log of all agents' actions every step."""
        save_step_metadata: bool = False
        """Whether to save the RL agents' action, environment state, and other data at every single step."""
        save_pcap_logs: bool = True
        """Whether to save PCAP logs."""
        save_sys_logs: bool = True
        """Whether to save system logs."""
        write_sys_log_to_terminal: bool = False
        """Whether to write the sys log to the terminal."""
        sys_log_level: LogLevel = LogLevel.INFO
        """The level of log that should be included in the logfiles/logged into terminal."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        """
        Init the PrimaiteIO object.

        Note: Instantiating this object creates a new directory for outputs, and sets the global SIM_OUTPUT variable.
        It is intended that this object is instantiated when a new environment is created.
        """
        self.settings = settings or PrimaiteIO.Settings()
        self.session_path: Path = self.generate_session_path()
        # set global SIM_OUTPUT path
        SIM_OUTPUT.path = self.session_path / "simulation_output"
        SIM_OUTPUT.save_pcap_logs = self.settings.save_pcap_logs
        SIM_OUTPUT.save_sys_logs = self.settings.save_sys_logs
        SIM_OUTPUT.write_sys_log_to_terminal = self.settings.write_sys_log_to_terminal
        SIM_OUTPUT.sys_log_level = self.settings.sys_log_level

    def generate_session_path(self, timestamp: Optional[datetime] = None) -> Path:
        """Create a folder for the session and return the path to it."""
        if timestamp is None:
            timestamp = datetime.now()
        date_str = timestamp.strftime("%Y-%m-%d")
        time_str = timestamp.strftime("%H-%M-%S")

        session_path = PRIMAITE_PATHS.user_sessions_path / date_str / time_str

        # check if running in dev mode
        if is_dev_mode():
            # check if there is an output directory set in config
            session_path = _PRIMAITE_ROOT.parent.parent / "sessions" / date_str / time_str

        session_path.mkdir(exist_ok=True, parents=True)
        return session_path

    def generate_model_save_path(self, agent_name: str) -> Path:
        """Return the path where the final model will be saved (excluding filename extension)."""
        return self.session_path / "checkpoints" / f"{agent_name}_final"

    def generate_checkpoint_save_path(self, agent_name: str, episode: int) -> Path:
        """Return the path where the checkpoint model will be saved (excluding filename extension)."""
        return self.session_path / "checkpoints" / f"{agent_name}_checkpoint_{episode}.pt"

    def generate_agent_actions_save_path(self, episode: int) -> Path:
        """Return the path where agent actions will be saved."""
        return self.session_path / "agent_actions" / f"episode_{episode}.json"

    def write_agent_actions(self, agent_actions: Dict[str, List], episode: int) -> None:
        """Take the contents of the agent action log and write it to a file.

        :param episode: Episode number
        :type episode: int
        """
        data = {}
        longest_history = max([len(hist) for hist in agent_actions.values()])
        for i in range(longest_history):
            data[i] = {"timestep": i, "episode": episode}
            data[i].update({name: acts[i] for name, acts in agent_actions.items() if len(acts) > i})

        path = self.generate_agent_actions_save_path(episode=episode)
        path.parent.mkdir(exist_ok=True, parents=True)
        path.touch()
        _LOGGER.info(f"Saving agent action log to {path}")
        with open(path, "w") as file:
            json.dump(data, fp=file, indent=1, default=lambda x: x.model_dump())

    @classmethod
    def from_config(cls, config: Dict) -> "PrimaiteIO":
        """Create an instance of PrimaiteIO based on a configuration dict."""
        config = config or {}

        if config.get("sys_log_level"):
            config["sys_log_level"] = LogLevel[config["sys_log_level"].upper()]  # convert to enum

        new = cls(settings=cls.Settings(**config))

        return new
