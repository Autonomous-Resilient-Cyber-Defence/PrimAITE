# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
"""Manages the observation space for the agent."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Optional, Type, Union

from gymnasium import spaces
from gymnasium.core import ObsType
from pydantic import BaseModel, ConfigDict

from primaite import getLogger

_LOGGER = getLogger(__name__)
WhereType = Optional[Iterable[Union[str, int]]]


class AbstractObservation(ABC):
    """Abstract class for an observation space component."""

    class ConfigSchema(ABC, BaseModel):
        """Config schema for observations."""

        thresholds: Optional[Dict] = {}
        """A dict containing the observation thresholds."""

        model_config = ConfigDict(extra="forbid")

    _registry: Dict[str, Type["AbstractObservation"]] = {}
    """Registry of observation components, with their name as key.

    Automatically populated when subclasses are defined. Used for defining from_config.
    """

    def __init__(self) -> None:
        """Initialise an observation. This method must be overwritten."""
        self.default_observation: ObsType

    def __init_subclass__(cls, discriminator: Optional[str] = None, **kwargs: Any) -> None:
        """
        Register an observation type.

        :param discriminator: discriminator used to uniquely specify observation component types.
        :type discriminator: str
        :raises ValueError: When attempting to create a component with a name that is already in use.
        """
        super().__init_subclass__(**kwargs)
        if discriminator is None:
            return
        if discriminator in cls._registry:
            raise ValueError(f"Duplicate observation component type {discriminator}")
        cls._registry[discriminator] = cls

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

    def _validate_thresholds(self, thresholds: List[int] = None, threshold_identifier: Optional[str] = "") -> bool:
        """
        Method that checks if the thresholds are non overlapping and in the correct (ascending) order.

        Pass in the thresholds from low to high e.g.
        thresholds=[low_threshold, med_threshold, ..._threshold, high_threshold]

        Throws an error if the threshold is not valid

        :param: thresholds: List of thresholds in ascending order.
        :type: List[int]
        :param: threshold_identifier: The name of the threshold option.
        :type: Optional[str]

        :returns: bool
        """
        if thresholds is None or len(thresholds) < 2:
            raise Exception(f"{threshold_identifier} thresholds are invalid {thresholds}")
        for idx in range(1, len(thresholds)):
            if not isinstance(thresholds[idx], int):
                raise Exception(f"{threshold_identifier} threshold ({thresholds[idx]}) is not a valid int.")
            if not isinstance(thresholds[idx - 1], int):
                raise Exception(f"{threshold_identifier} threshold ({thresholds[idx]}) is not a valid int.")

            if thresholds[idx] <= thresholds[idx - 1]:
                raise Exception(
                    f"{threshold_identifier} threshold ({thresholds[idx - 1]}) "
                    f"is greater than or equal to ({thresholds[idx]}.)"
                )
        return True
