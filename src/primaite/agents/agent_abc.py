from abc import ABC, abstractmethod
from typing import Optional

from primaite.environment.primaite_env import Primaite


class AgentABC(ABC):

    @abstractmethod
    def __init__(self, env: Primaite):
        self._env: Primaite = env
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