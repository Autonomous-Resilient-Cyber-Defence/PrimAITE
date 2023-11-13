from abc import ABC, abstractclassmethod, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from primaite.game.session import PrimaiteSession


class PolicyABC(ABC):
    """Base class for reinforcement learning agents."""

    @abstractmethod
    def __init__(self, session: "PrimaiteSession") -> None:
        """Initialize a reinforcement learning agent."""
        self.session: "PrimaiteSession" = session
        pass

    @abstractmethod
    def learn(self, n_episodes: int, n_time_steps: int) -> None:
        """Train the agent."""
        pass

    @abstractmethod
    def eval(self, n_episodes: int, n_time_steps: int, deterministic: bool) -> None:
        """Evaluate the agent."""
        pass

    @abstractmethod
    def save(
        self,
    ) -> None:
        """Save the agent."""
        pass

    @abstractmethod
    def load(
        self,
    ) -> None:
        """Load agent from a file."""
        pass

    def close(
        self,
    ) -> None:
        """Close the agent."""
        pass

    @abstractclassmethod
    def from_config(
        cls,
    ) -> "PolicyABC":
        """Create an agent from a config file."""
        pass

    # saving checkpoints logic will be handled here, it will invoke 'save' method which is implemented by the subclass
