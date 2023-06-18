from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional, Final, Dict, Any, Union, Tuple

import yaml

from primaite import getLogger
from primaite.config.training_config import TrainingConfig, load
from primaite.environment.primaite_env import Primaite

_LOGGER = getLogger(__name__)


def _get_temp_session_path(session_timestamp: datetime) -> Path:
    """
    Get a temp directory session path the test session will output to.

    :param session_timestamp: This is the datetime that the session started.
    :return: The session directory path.
    """
    date_dir = session_timestamp.strftime("%Y-%m-%d")
    session_dir = session_timestamp.strftime("%Y-%m-%d_%H-%M-%S")
    session_path = Path("./") / date_dir / session_dir
    session_path.mkdir(exist_ok=True, parents=True)

    return session_path


class AgentABC(ABC):

    @abstractmethod
    def __init__(
            self,
            training_config_path,
            lay_down_config_path
    ):
        self._training_config_path = training_config_path
        self._training_config: Final[TrainingConfig] = load(
            self._training_config_path
        )
        self._lay_down_config_path = lay_down_config_path
        self._env: Primaite
        self._agent = None
        self.session_timestamp: datetime = datetime.now()
        self.session_path = _get_temp_session_path(self.session_timestamp)

        self.timestamp_str = self.session_timestamp.strftime(
            "%Y-%m-%d_%H-%M-%S")

    @abstractmethod
    def _setup(self):
        pass

    @abstractmethod
    def _save_checkpoint(self):
        pass

    @abstractmethod
    def learn(
            self,
            time_steps: Optional[int] = None,
            episodes: Optional[int] = None
    ):
        pass

    @abstractmethod
    def evaluate(
            self,
            time_steps: Optional[int] = None,
            episodes: Optional[int] = None
    ):
        pass

    @abstractmethod
    def _get_latest_checkpoint(self):
        pass

    @classmethod
    @abstractmethod
    def load(cls):
        pass

    @abstractmethod
    def save(self):
        pass

    @abstractmethod
    def export(self):
        pass


class DeterministicAgentABC(AgentABC):
    @abstractmethod
    def __init__(
            self,
            training_config_path,
            lay_down_config_path
    ):
        self._training_config_path = training_config_path
        self._lay_down_config_path = lay_down_config_path
        self._env: Primaite
        self._agent = None

    @abstractmethod
    def _setup(self):
        pass

    @abstractmethod
    def _get_latest_checkpoint(self):
        pass

    def learn(self, time_steps: Optional[int], episodes: Optional[int]):
        pass
        _LOGGER.warning("Deterministic agents cannot learn")

    @abstractmethod
    def evaluate(self, time_steps: Optional[int], episodes: Optional[int]):
        pass

    @classmethod
    @abstractmethod
    def load(cls):
        pass

    @abstractmethod
    def save(self):
        pass

    @abstractmethod
    def export(self):
        pass
