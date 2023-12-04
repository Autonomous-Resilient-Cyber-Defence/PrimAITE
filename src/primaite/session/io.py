from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict

from primaite import PRIMAITE_PATHS
from primaite.simulator import SIM_OUTPUT


class SessionIOSettings(BaseModel):
    """Schema for session IO settings."""

    model_config = ConfigDict(extra="forbid")

    save_final_model: bool = True
    """Whether to save the final model right at the end of training."""
    save_checkpoints: bool = False
    """Whether to save a checkpoint model every `checkpoint_interval` episodes"""
    checkpoint_interval: int = 10
    """How often to save a checkpoint model (if save_checkpoints is True)."""
    save_logs: bool = True
    """Whether to save logs"""
    save_transactions: bool = True
    """Whether to save transactions, If true, the session path will have a transactions folder."""
    save_tensorboard_logs: bool = False
    """Whether to save tensorboard logs. If true, the session path will have a tenorboard_logs folder."""
    save_step_metadata: bool = False
    """Whether to save the RL agents' action, environment state, and other data at every single step."""


class SessionIO:
    """
    Class for managing session IO.

    Currently it's handling path generation, but could expand to handle loading, transaction, tensorboard, and so on.
    """

    def __init__(self, settings: SessionIOSettings = SessionIOSettings()) -> None:
        self.settings: SessionIOSettings = settings
        self.session_path: Path = self.generate_session_path()

        # set global SIM_OUTPUT path
        SIM_OUTPUT.path = self.session_path / "simulation_output"

        # warning TODO: must be careful not to re-initialise sessionIO because it will create a new path each time it's
        # possible refactor needed

    def generate_session_path(self, timestamp: Optional[datetime] = None) -> Path:
        """Create a folder for the session and return the path to it."""
        if timestamp is None:
            timestamp = datetime.now()
        date_str = timestamp.strftime("%Y-%m-%d")
        time_str = timestamp.strftime("%H-%M-%S")
        session_path = PRIMAITE_PATHS.user_sessions_path / date_str / time_str
        session_path.mkdir(exist_ok=True, parents=True)
        return session_path

    def generate_model_save_path(self, agent_name: str) -> Path:
        """Return the path where the final model will be saved (excluding filename extension)."""
        return self.session_path / "checkpoints" / f"{agent_name}_final"

    def generate_checkpoint_save_path(self, agent_name: str, episode: int) -> Path:
        """Return the path where the checkpoint model will be saved (excluding filename extension)."""
        return self.session_path / "checkpoints" / f"{agent_name}_checkpoint_{episode}.pt"
