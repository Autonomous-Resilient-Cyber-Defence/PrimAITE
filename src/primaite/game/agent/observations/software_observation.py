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
        return spaces.Dict({"operating_status": spaces.Discrete(7), "health_status": spaces.Discrete(5)})

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


class ApplicationObservation(AbstractObservation):
    """Observation of an application in the network."""

    default_observation: spaces.Space = {"operating_status": 0, "health_status": 0, "num_executions": 0}
    "Default observation is what should be returned when the application doesn't exist."

    def __init__(self, where: Optional[Tuple[str]] = None) -> None:
        """Initialise application observation.

        :param where: Store information about where in the simulation state dictionary to find the relevant information.
            Optional. If None, this corresponds that the file does not exist and the observation will be populated with
            zeroes.

            A typical location for a service looks like this:
            `['network','nodes',<node_hostname>,'applications', <application_name>]`
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

        app_state = access_from_nested_dict(state, self.where)
        if app_state is NOT_PRESENT_IN_STATE:
            return self.default_observation
        return {
            "operating_status": app_state["operating_state"],
            "health_status": app_state["health_state_visible"],
            "num_executions": self._categorise_num_executions(app_state["num_executions"]),
        }

    @property
    def space(self) -> spaces.Space:
        """Gymnasium space object describing the observation space shape."""
        return spaces.Dict(
            {
                "operating_status": spaces.Discrete(7),
                "health_status": spaces.Discrete(6),
                "num_executions": spaces.Discrete(4),
            }
        )

    @classmethod
    def from_config(
        cls, config: Dict, game: "PrimaiteGame", parent_where: Optional[List[str]] = None
    ) -> "ApplicationObservation":
        """Create application observation from a config.

        :param config: Dictionary containing the configuration for this service observation.
        :type config: Dict
        :param game: Reference to the PrimaiteGame object that spawned this observation.
        :type game: PrimaiteGame
        :param parent_where: Where in the simulation state dictionary this service's parent node is located. Optional.
        :type parent_where: Optional[List[str]], optional
        :return: Constructed service observation
        :rtype: ApplicationObservation
        """
        return cls(where=parent_where + ["services", config["application_name"]])

    @classmethod
    def _categorise_num_executions(cls, num_executions: int) -> int:
        """
        Categorise the number of executions of an application.

        Helps classify the number of application executions into different categories.

        Current categories:
        - 0: Application is never executed
        - 1: Application is executed a low number of times (1-5)
        - 2: Application is executed often (6-10)
        - 3: Application is executed a high number of times (more than 10)

        :param: num_executions: Number of times the application is executed
        """
        if num_executions > 10:
            return 3
        elif num_executions > 5:
            return 2
        elif num_executions > 0:
            return 1
        return 0
