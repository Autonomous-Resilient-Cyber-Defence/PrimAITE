from abc import ABC, abstractmethod
from typing import Optional, Final, Dict, Any

from primaite import getLogger
from primaite.config.training_config import TrainingConfig
from primaite.environment.primaite_env import Primaite

_LOGGER = getLogger(__name__)


class AgentABC(ABC):

    @abstractmethod
    def __init__(self, env: Primaite):
        self._env: Primaite = env
        self._training_config: Final[TrainingConfig] = self._env.training_config
        self._lay_down_config: Dict[str, Any] = self._env.lay_down_config
        self._agent = None

    @abstractmethod
    def _setup(self):
        pass

    @abstractmethod
    def learn(self, time_steps: Optional[int], episodes: Optional[int]):
        pass

    @abstractmethod
    def evaluate(self, time_steps: Optional[int], episodes: Optional[int]):
        pass

    @abstractmethod
    def load(self):
        pass

    @abstractmethod
    def save(self):
        pass

    @abstractmethod
    def export(self):
        pass


class DeterministicAgentABC(AgentABC):
    @abstractmethod
    def __init__(self, env: Primaite):
        self._env: Primaite = env
        self._agent = None

    @abstractmethod
    def _setup(self):
        pass

    def learn(self, time_steps: Optional[int], episodes: Optional[int]):
        pass
        _LOGGER.warning("Deterministic agents cannot learn")

    @abstractmethod
    def evaluate(self, time_steps: Optional[int], episodes: Optional[int]):
        pass

    @abstractmethod
    def load(self):
        pass

    @abstractmethod
    def save(self):
        pass

    @abstractmethod
    def export(self):
        pass
