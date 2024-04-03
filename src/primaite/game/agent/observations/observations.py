"""Manages the observation space for the agent."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, Type

from gymnasium import spaces
from gymnasium.core import ObsType
from pydantic import BaseModel, ConfigDict

from primaite import getLogger

_LOGGER = getLogger(__name__)
WhereType = Iterable[str | int] | None


class AbstractObservation(ABC):
    """Abstract class for an observation space component."""

    class ConfigSchema(ABC, BaseModel):
        """Config schema for observations."""

        model_config = ConfigDict(extra="forbid")

    _registry: Dict[str, Type["AbstractObservation"]] = {}
    """Registry of observation components, with their name as key.

    Automatically populated when subclasses are defined. Used for defining from_config.
    """

    def __init__(self) -> None:
        """Initialise an observation. This method must be overwritten."""
        self.default_observation: ObsType

    def __init_subclass__(cls, identifier: str, **kwargs: Any) -> None:
        """
        Register an observation type.

        :param identifier: Identifier used to uniquely specify observation component types.
        :type identifier: str
        :raises ValueError: When attempting to create a component with a name that is already in use.
        """
        super().__init_subclass__(**kwargs)
        if identifier in cls._registry:
            raise ValueError(f"Duplicate observation component type {identifier}")
        cls._registry[identifier] = cls

    @abstractmethod
    def observe(self, state: Dict) -> Any:
        """
        Return an observation based on the current state of the simulation.

        :param state: Simulation state dictionary
        :type state: Dict
        :return: Observation
        :rtype: Any
        """
        pass

    @property
    @abstractmethod
    def space(self) -> spaces.Space:
        """Gymnasium space object describing the observation space."""
        pass

    @classmethod
    @abstractmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = []) -> "AbstractObservation":
        """Create this observation space component form a serialised format."""
        return cls()
