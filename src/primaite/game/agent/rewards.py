"""
Manages the reward function for the agent.

Each agent is equipped with a RewardFunction, which is made up of a list of reward components. The components are
designed to calculate a reward value based on the current state of the simulation. The overall reward function is a
weighed sum of the components.

The reward function is typically specified using a config yaml file or a config dictionary. The following example shows
the structure:
```yaml
    reward_function:
        reward_components:
            - type: DATABASE_FILE_INTEGRITY
            weight: 0.5
            options:
                node_ref: database_server
                folder_name: database
                file_name: database.db


            - type: WEB_SERVER_404_PENALTY
            weight: 0.5
            options:
                node_ref: web_server
                service_ref: web_server_database_client
```
"""
from abc import abstractmethod
from typing import Dict, List, Tuple, Type, TYPE_CHECKING

from primaite import getLogger
from primaite.game.agent.utils import access_from_nested_dict, NOT_PRESENT_IN_STATE

_LOGGER = getLogger(__name__)

if TYPE_CHECKING:
    from primaite.game.game import PrimaiteGame


class AbstractReward:
    """Base class for reward function components."""

    @abstractmethod
    def calculate(self, state: Dict) -> float:
        """Calculate the reward for the current state."""
        return 0.0

    @classmethod
    @abstractmethod
    def from_config(cls, config: dict, game: "PrimaiteGame") -> "AbstractReward":
        """Create a reward function component from a config dictionary.

        :param config: dict of options for the reward component's constructor
        :type config: dict
        :param game: Reference to the PrimAITE Game object
        :type game: PrimaiteGame
        :return: The reward component.
        :rtype: AbstractReward
        """
        return cls()


class DummyReward(AbstractReward):
    """Dummy reward function component which always returns 0."""

    def calculate(self, state: Dict) -> float:
        """Calculate the reward for the current state."""
        return 0.0

    @classmethod
    def from_config(cls, config: dict, game: "PrimaiteGame") -> "DummyReward":
        """Create a reward function component from a config dictionary.

        :param config: dict of options for the reward component's constructor. Should be empty.
        :type config: dict
        :param game: Reference to the PrimAITE Game object
        :type game: PrimaiteGame
        """
        return cls()


class DatabaseFileIntegrity(AbstractReward):
    """Reward function component which rewards the agent for maintaining the integrity of a database file."""

    def __init__(self, node_uuid: str, folder_name: str, file_name: str) -> None:
        """Initialise the reward component.

        :param node_uuid: UUID of the node which contains the database file.
        :type node_uuid: str
        :param folder_name: folder which contains the database file.
        :type folder_name: str
        :param file_name: name of the database file.
        :type file_name: str
        """
        self.location_in_state = [
            "network",
            "nodes",
            node_uuid,
            "file_system",
            "folders",
            folder_name,
            "files",
            file_name,
        ]

    def calculate(self, state: Dict) -> float:
        """Calculate the reward for the current state.

        :param state: The current state of the simulation.
        :type state: Dict
        """
        database_file_state = access_from_nested_dict(state, self.location_in_state)
        health_status = database_file_state["health_status"]
        if health_status == "corrupted":
            return -1
        elif health_status == "good":
            return 1
        else:
            return 0

    @classmethod
    def from_config(cls, config: Dict, game: "PrimaiteGame") -> "DatabaseFileIntegrity":
        """Create a reward function component from a config dictionary.

        :param config: dict of options for the reward component's constructor
        :type config: Dict
        :param game: Reference to the PrimAITE Game object
        :type game: PrimaiteGame
        :return: The reward component.
        :rtype: DatabaseFileIntegrity
        """
        node_ref = config.get("node_ref")
        folder_name = config.get("folder_name")
        file_name = config.get("file_name")
        if not node_ref:
            _LOGGER.error(
                f"{cls.__name__} could not be initialised from config because node_ref parameter was not specified"
            )
            return DummyReward()  # TODO: better error handling
        if not folder_name:
            _LOGGER.error(
                f"{cls.__name__} could not be initialised from config because folder_name parameter was not specified"
            )
            return DummyReward()  # TODO: better error handling
        if not file_name:
            _LOGGER.error(
                f"{cls.__name__} could not be initialised from config because file_name parameter was not specified"
            )
            return DummyReward()  # TODO: better error handling
        node_uuid = game.ref_map_nodes[node_ref]
        if not node_uuid:
            _LOGGER.error(
                (
                    f"{cls.__name__} could not be initialised from config because the referenced node could not be "
                    f"found in the simulation"
                )
            )
            return DummyReward()  # TODO: better error handling

        return cls(node_uuid=node_uuid, folder_name=folder_name, file_name=file_name)


class WebServer404Penalty(AbstractReward):
    """Reward function component which penalises the agent when the web server returns a 404 error."""

    def __init__(self, node_uuid: str, service_uuid: str) -> None:
        """Initialise the reward component.

        :param node_uuid: UUID of the node which contains the web server service.
        :type node_uuid: str
        :param service_uuid: UUID of the web server service.
        :type service_uuid: str
        """
        self.location_in_state = ["network", "nodes", node_uuid, "services", service_uuid]

    def calculate(self, state: Dict) -> float:
        """Calculate the reward for the current state.

        :param state: The current state of the simulation.
        :type state: Dict
        """
        web_service_state = access_from_nested_dict(state, self.location_in_state)
        if web_service_state is NOT_PRESENT_IN_STATE:
            print("error getting web service state")
            return 0.0
        most_recent_return_code = web_service_state["last_response_status_code"]
        # TODO: reward needs to use the current web state. Observation should return web state at the time of last scan.
        if most_recent_return_code == 200:
            return 1.0
        elif most_recent_return_code == 404:
            return -1.0
        else:
            return 0.0

    @classmethod
    def from_config(cls, config: Dict, game: "PrimaiteGame") -> "WebServer404Penalty":
        """Create a reward function component from a config dictionary.

        :param config: dict of options for the reward component's constructor
        :type config: Dict
        :param game: Reference to the PrimAITE Game object
        :type game: PrimaiteGame
        :return: The reward component.
        :rtype: WebServer404Penalty
        """
        node_ref = config.get("node_ref")
        service_ref = config.get("service_ref")
        if not (node_ref and service_ref):
            msg = (
                f"{cls.__name__} could not be initialised from config because node_ref and service_ref were not "
                "found in reward config."
            )
            _LOGGER.warning(msg)
            return DummyReward()  # TODO: should we error out with incorrect inputs? Probably!
        node_uuid = game.ref_map_nodes[node_ref]
        service_uuid = game.ref_map_services[service_ref]
        if not (node_uuid and service_uuid):
            msg = (
                f"{cls.__name__} could not be initialised because node {node_ref} and service {service_ref} were not"
                " found in the simulator."
            )
            _LOGGER.warning(msg)
            return DummyReward()  # TODO: consider erroring here as well

        return cls(node_uuid=node_uuid, service_uuid=service_uuid)


class RewardFunction:
    """Manages the reward function for the agent."""

    __rew_class_identifiers: Dict[str, Type[AbstractReward]] = {
        "DUMMY": DummyReward,
        "DATABASE_FILE_INTEGRITY": DatabaseFileIntegrity,
        "WEB_SERVER_404_PENALTY": WebServer404Penalty,
    }

    def __init__(self):
        """Initialise the reward function object."""
        self.reward_components: List[Tuple[AbstractReward, float]] = []
        "attribute reward_components keeps track of reward components and the weights assigned to each."
        self.current_reward: float
        self.total_reward: float = 0.0

    def regsiter_component(self, component: AbstractReward, weight: float = 1.0) -> None:
        """Add a reward component to the reward function.

        :param component: Instance of a reward component.
        :type component: AbstractReward
        :param weight: Relative weight of the reward component, defaults to 1.0
        :type weight: float, optional
        """
        self.reward_components.append((component, weight))

    def update(self, state: Dict) -> float:
        """Calculate the overall reward for the current state.

        :param state: The current state of the simulation.
        :type state: Dict
        """
        total = 0.0
        for comp_and_weight in self.reward_components:
            comp = comp_and_weight[0]
            weight = comp_and_weight[1]
            total += weight * comp.calculate(state=state)
        self.current_reward = total
        return self.current_reward

    @classmethod
    def from_config(cls, config: Dict, game: "PrimaiteGame") -> "RewardFunction":
        """Create a reward function from a config dictionary.

        :param config: dict of options for the reward manager's constructor
        :type config: Dict
        :param game: Reference to the PrimAITE Game object
        :type game: PrimaiteGame
        :return: The reward manager.
        :rtype: RewardFunction
        """
        new = cls()

        for rew_component_cfg in config["reward_components"]:
            rew_type = rew_component_cfg["type"]
            weight = rew_component_cfg.get("weight", 1.0)
            rew_class = cls.__rew_class_identifiers[rew_type]
            rew_instance = rew_class.from_config(config=rew_component_cfg.get("options", {}), game=game)
            new.regsiter_component(component=rew_instance, weight=weight)
        return new
