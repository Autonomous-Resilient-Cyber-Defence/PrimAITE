from typing import Dict, TYPE_CHECKING

from gymnasium.core import ObsType

from primaite.game.agent.observations.agent_observations import (
    UC2BlueObservation,
    UC2GreenObservation,
    UC2RedObservation,
)
from primaite.game.agent.observations.observations import AbstractObservation

if TYPE_CHECKING:
    from primaite.game.game import PrimaiteGame


class ObservationManager:
    """
    Manage the observations of an Agent.

    The observation space has the purpose of:
      1. Reading the outputted state from the PrimAITE Simulation.
      2. Selecting parts of the simulation state that are requested by the simulation config
      3. Formatting this information so an agent can use it to make decisions.
    """

    # TODO: Dear code reader: This class currently doesn't do much except hold an observation object. It will be changed
    # to have more of it's own behaviour, and it will replace UC2BlueObservation and UC2RedObservation during the next
    # refactor.

    def __init__(self, observation: AbstractObservation) -> None:
        """Initialise observation space.

        :param observation: Observation object
        :type observation: AbstractObservation
        """
        self.obs: AbstractObservation = observation
        self.current_observation: ObsType

    def update(self, state: Dict) -> Dict:
        """
        Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary
        :type state: Dict
        """
        self.current_observation = self.obs.observe(state)
        return self.current_observation

    @property
    def space(self) -> None:
        """Gymnasium space object describing the observation space shape."""
        return self.obs.space

    @classmethod
    def from_config(cls, config: Dict, game: "PrimaiteGame") -> "ObservationManager":
        """Create observation space from a config.

        :param config: Dictionary containing the configuration for this observation space.
            It should contain the key 'type' which selects which observation class to use (from a choice of:
            UC2BlueObservation, UC2RedObservation, UC2GreenObservation)
            The other key is 'options' which are passed to the constructor of the selected observation class.
        :type config: Dict
        :param game: Reference to the PrimaiteGame object that spawned this observation.
        :type game: PrimaiteGame
        """
        if config["type"] == "UC2BlueObservation":
            return cls(UC2BlueObservation.from_config(config.get("options", {}), game=game))
        elif config["type"] == "UC2RedObservation":
            return cls(UC2RedObservation.from_config(config.get("options", {}), game=game))
        elif config["type"] == "UC2GreenObservation":
            return cls(UC2GreenObservation.from_config(config.get("options", {}), game=game))
        else:
            raise ValueError("Observation space type invalid")
