from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from gymnasium import spaces

from primaite.game.agent.observations.observations import AbstractObservation
from primaite.game.agent.utils import access_from_nested_dict, NOT_PRESENT_IN_STATE

if TYPE_CHECKING:
    from primaite.game.game import PrimaiteGame


class ServiceObservation(AbstractObservation):
    """Observation of a service in the network."""

    default_observation: spaces.Space = {"operating_status": 0, "health_status": 0}
    "Default observation is what should be returned when the service doesn't exist."

    def __init__(self, where: Optional[Tuple[str]] = None) -> None:
        """Initialise service observation.

        :param where: Store information about where in the simulation state dictionary to find the relevant information.
            Optional. If None, this corresponds that the file does not exist and the observation will be populated with
            zeroes.

            A typical location for a service looks like this:
            `['network','nodes',<node_hostname>,'services', <service_name>]`
        :type where: Optional[List[str]]
        """
        super().__init__()
        self.where: Optional[Tuple[str]] = where

    def observe(self, state: Dict) -> Dict:
        """Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary
        :type state: Dict
        :return: Observation
        :rtype: Dict
        """
        if self.where is None:
            return self.default_observation

        service_state = access_from_nested_dict(state, self.where)
        if service_state is NOT_PRESENT_IN_STATE:
            return self.default_observation
        return {
            "operating_status": service_state["operating_state"],
            "health_status": service_state["health_state_visible"],
        }

    @property
    def space(self) -> spaces.Space:
        """Gymnasium space object describing the observation space shape."""
        return spaces.Dict({"operating_status": spaces.Discrete(7), "health_status": spaces.Discrete(6)})

    @classmethod
    def from_config(
        cls, config: Dict, game: "PrimaiteGame", parent_where: Optional[List[str]] = None
    ) -> "ServiceObservation":
        """Create service observation from a config.

        :param config: Dictionary containing the configuration for this service observation.
        :type config: Dict
        :param game: Reference to the PrimaiteGame object that spawned this observation.
        :type game: PrimaiteGame
        :param parent_where: Where in the simulation state dictionary this service's parent node is located. Optional.
        :type parent_where: Optional[List[str]], optional
        :return: Constructed service observation
        :rtype: ServiceObservation
        """
        return cls(where=parent_where + ["services", config["service_name"]])
