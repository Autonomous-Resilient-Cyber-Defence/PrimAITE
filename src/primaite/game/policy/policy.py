"""Base class and common logic for RL policies."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from primaite.game.session import PrimaiteSession, TrainingOptions


class PolicyABC(ABC):
    """Base class for reinforcement learning agents."""

    _registry: Dict[str, type["PolicyABC"]] = {}
    """
    Registry of policy types, keyed by name.

    Automatically populated when PolicyABC subclasses are defined. Used for defining from_config.
    """

    def __init_subclass__(cls, identifier: str, **kwargs: Any) -> None:
        """
        Register a policy subclass.

        :param name: Identifier used by from_config to create an instance of the policy.
        :type name: str
        :raises ValueError: When attempting to create a policy with a duplicate name.
        """
        super().__init_subclass__(**kwargs)
        if identifier in cls._registry:
            raise ValueError(f"Duplicate policy name {identifier}")
        cls._registry[identifier] = cls
        return

    @abstractmethod
    def __init__(self, session: "PrimaiteSession") -> None:
        """
        Initialize a reinforcement learning policy.

        :param session: The session context.
        :type session: PrimaiteSession
        :param agents: The agents to train.
        :type agents: List[RLAgent]
        """
        self.session: "PrimaiteSession" = session
        """Reference to the session."""

    @abstractmethod
    def learn(self, n_episodes: int, n_time_steps: int) -> None:
        """Train the agent."""
        pass

    @abstractmethod
    def eval(self, n_episodes: int, n_time_steps: int, deterministic: bool) -> None:
        """Evaluate the agent."""
        pass

    @abstractmethod
    def save(self, save_path: Path) -> None:
        """Save the agent."""
        pass

    @abstractmethod
    def load(self) -> None:
        """Load agent from a file."""
        pass

    def close(self) -> None:
        """Close the agent."""
        pass

    @classmethod
    def from_config(cls, config: "TrainingOptions", session: "PrimaiteSession") -> "PolicyABC":
        """
        Create an RL policy from a config by calling the relevant subclass's from_config method.

        Subclasses should not call super().from_config(), they should just handle creation form config.
        """
        # Assume that basically the contents of training_config are passed into here.
        # I should really define a config schema class using pydantic.

        PolicyType = cls._registry[config.rl_framework]
        return PolicyType.from_config(config=config, session=session)

    # saving checkpoints logic will be handled here, it will invoke 'save' method which is implemented by the subclass
