# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
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
                node_name: database_server
                folder_name: database
                file_name: database.db


            - type: WEB_SERVER_404_PENALTY
            weight: 0.5
            options:
                node_name: web_server
                service_ref: web_server_database_client
```
"""
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Callable, Dict, Iterable, List, Optional, Tuple, Type, TYPE_CHECKING, Union

from pydantic import BaseModel
from typing_extensions import Never

from primaite import getLogger
from primaite.game.agent.utils import access_from_nested_dict, NOT_PRESENT_IN_STATE

if TYPE_CHECKING:
    from primaite.game.agent.interface import AgentHistoryItem

_LOGGER = getLogger(__name__)
WhereType = Optional[Iterable[Union[str, int]]]


class AbstractReward(BaseModel):
    """Base class for reward function components."""

    class ConfigSchema(BaseModel, ABC):
        """Config schema for AbstractReward."""

        type: str

    _registry: ClassVar[Dict[str, Type["AbstractReward"]]] = {}

    def __init_subclass__(cls, identifier: str, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if identifier in cls._registry:
            raise ValueError(f"Duplicate node adder {identifier}")
        cls._registry[identifier] = cls

    @classmethod
    def from_config(cls, config: Dict) -> "AbstractReward":
        """Create a reward function component from a config dictionary.

        :param config: dict of options for the reward component's constructor
        :type config: dict
        :return: The reward component.
        :rtype: AbstractReward
        """
        if config["type"] not in cls._registry:
            raise ValueError(f"Invalid reward type {config['type']}")
        adder_class = cls._registry[config["type"]]
        adder_class.add_nodes_to_net(config=adder_class.ConfigSchema(**config))
        return cls

    @abstractmethod
    def calculate(self, state: Dict, last_action_response: "AgentHistoryItem") -> float:
        """Calculate the reward for the current state.

        :param state: Current simulation state
        :type state: Dict
        :param last_action_response: Current agent history state
        :type last_action_response: AgentHistoryItem state
        :return: Reward value
        :rtype: float
        """
        return 0.0


class DummyReward(AbstractReward, identifier="DummyReward"):
    """Dummy reward function component which always returns 0.0."""

    def calculate(self, state: Dict, last_action_response: "AgentHistoryItem") -> float:
        """Calculate the reward for the current state.

        :param state: Current simulation state
        :type state: Dict
        :param last_action_response: Current agent history state
        :type last_action_response: AgentHistoryItem state
        :return: Reward value
        :rtype: float
        """
        return 0.0

    @classmethod
    def from_config(cls, config: dict) -> "DummyReward":
        """Create a reward function component from a config dictionary.

        :param config: dict of options for the reward component's constructor. Should be empty.
        :type config: dict
        :return: The reward component.
        :rtype: DummyReward
        """
        return cls()


class DatabaseFileIntegrity(AbstractReward, identifier="DatabaseFileIntegrity"):
    """Reward function component which rewards the agent for maintaining the integrity of a database file."""

    class ConfigSchema(AbstractReward.ConfigSchema):
        """ConfigSchema for DatabaseFileIntegrity."""

        node_hostname: str
        folder_name: str
        file_name: str

    def __init__(self, node_hostname: str, folder_name: str, file_name: str) -> None:
        """Initialise the reward component.

        :param node_hostname: Hostname of the node which contains the database file.
        :type node_hostname: str
        :param folder_name: folder which contains the database file.
        :type folder_name: str
        :param file_name: name of the database file.
        :type file_name: str
        """
        self.location_in_state = [
            "network",
            "nodes",
            node_hostname,
            "file_system",
            "folders",
            folder_name,
            "files",
            file_name,
        ]

    def calculate(self, state: Dict, last_action_response: "AgentHistoryItem") -> float:
        """Calculate the reward for the current state.

        :param state: Current simulation state
        :type state: Dict
        :param last_action_response: Current agent history state
        :type last_action_response: AgentHistoryItem state
        :return: Reward value
        :rtype: float
        """
        database_file_state = access_from_nested_dict(state, self.location_in_state)
        if database_file_state is NOT_PRESENT_IN_STATE:
            _LOGGER.debug(
                f"Could not calculate {self.__class__} reward because "
                "simulation state did not contain enough information."
            )
            return 0.0

        health_status = database_file_state["health_status"]
        if health_status == 2:
            return -1
        elif health_status == 1:
            return 1
        else:
            return 0

    @classmethod
    def from_config(cls, config: Dict) -> "DatabaseFileIntegrity":
        """Create a reward function component from a config dictionary.

        :param config: dict of options for the reward component's constructor
        :type config: Dict
        :return: The reward component.
        :rtype: DatabaseFileIntegrity
        """
        node_hostname = config.get("node_hostname")
        folder_name = config.get("folder_name")
        file_name = config.get("file_name")
        if not (node_hostname and folder_name and file_name):
            msg = f"{cls.__name__} could not be initialised with parameters {config}"
            _LOGGER.error(msg)
            raise ValueError(msg)

        return cls(node_hostname=node_hostname, folder_name=folder_name, file_name=file_name)


class WebServer404Penalty(AbstractReward, identifier="WebServer404Penalty"):
    """Reward function component which penalises the agent when the web server returns a 404 error."""

    class ConfigSchema(AbstractReward.ConfigSchema):
        """ConfigSchema for WebServer404Penalty."""

        node_hostname: str
        service_name: str
        sticky: bool = True

    def __init__(self, node_hostname: str, service_name: str, sticky: bool = True) -> None:
        """Initialise the reward component.

        :param node_hostname: Hostname of the node which contains the web server service.
        :type node_hostname: str
        :param service_name: Name of the web server service.
        :type service_name: str
        :param sticky: If True, calculate the reward based on the most recent response status. If False, only calculate
            the reward if there were any responses this timestep.
        :type sticky: bool
        """
        self.sticky: bool = sticky
        self.reward: float = 0.0
        """Reward value calculated last time any responses were seen. Used for persisting sticky rewards."""
        self.location_in_state = ["network", "nodes", node_hostname, "services", service_name]

    def calculate(self, state: Dict, last_action_response: "AgentHistoryItem") -> float:
        """Calculate the reward for the current state.

        :param state: Current simulation state
        :type state: Dict
        :param last_action_response: Current agent history state
        :type last_action_response: AgentHistoryItem state
        :return: Reward value
        :rtype: float
        """
        web_service_state = access_from_nested_dict(state, self.location_in_state)

        # if webserver is no longer installed on the node, return 0
        if web_service_state is NOT_PRESENT_IN_STATE:
            return 0.0

        codes = web_service_state.get("response_codes_this_timestep")
        if codes:

            def status2rew(status: int) -> int:
                """Map status codes to reward values."""
                return 1.0 if status == 200 else -1.0 if status == 404 else 0.0

            self.reward = sum(map(status2rew, codes)) / len(codes)  # convert form HTTP codes to rewards and average
        elif not self.sticky:  # there are no codes, but reward is not sticky, set reward to 0
            self.reward = 0.0
        else:  # skip calculating if sticky and no new codes. instead, reuse last step's value
            pass

        return self.reward

    @classmethod
    def from_config(cls, config: Dict) -> "WebServer404Penalty":
        """Create a reward function component from a config dictionary.

        :param config: dict of options for the reward component's constructor
        :type config: Dict
        :return: The reward component.
        :rtype: WebServer404Penalty
        """
        node_hostname = config.get("node_hostname")
        service_name = config.get("service_name")
        if not (node_hostname and service_name):
            msg = (
                f"{cls.__name__} could not be initialised from config because node_name and service_ref were not "
                "found in reward config."
            )
            _LOGGER.warning(msg)
            raise ValueError(msg)
        sticky = config.get("sticky", True)

        return cls(node_hostname=node_hostname, service_name=service_name, sticky=sticky)


class WebpageUnavailablePenalty(AbstractReward, identifier="WebpageUnavailablePenalty"):
    """Penalises the agent when the web browser fails to fetch a webpage."""
    node_hostname: str = ""
    sticky: bool = True
    reward: float = 0.0
    location_in_state: List[str] = [""]
    _node: str = node_hostname

    class ConfigSchema(AbstractReward.ConfigSchema):
        """ConfigSchema for WebpageUnavailablePenalty."""

        node_hostname: str = ""
        sticky: bool = True
        reward: float = 0.0

    # def __init__(self, node_hostname: str, sticky: bool = True) -> None:
    #     """
    #     Initialise the reward component.

    #     :param node_hostname: Hostname of the node which has the web browser.
    #     :type node_hostname: str
    #     :param sticky: If True, calculate the reward based on the most recent response status. If False, only calculate
    #         the reward if there were any responses this timestep.
    #     :type sticky: bool
    #     """
    #     self._node: str = node_hostname
    #     self.location_in_state: List[str] = ["network", "nodes", node_hostname, "applications", "WebBrowser"]
    #     self.sticky: bool = sticky
    #     self.reward: float = 0.0
    #     """Reward value calculated last time any responses were seen. Used for persisting sticky rewards."""

    def calculate(self, state: Dict, last_action_response: "AgentHistoryItem") -> float:
        """
        Calculate the reward based on current simulation state, and the recent agent action.

        When the green agent requests to execute the browser application, and that request fails, this reward
        component will keep track of that information. In that case, it doesn't matter whether the last webpage
        had a 200 status code, because there has been an unsuccessful request since.
        :param state: Current simulation state
        :type state: Dict
        :param last_action_response: Current agent history state
        :type last_action_response: AgentHistoryItem state
        :return: Reward value
        :rtype: float
        """
        self.location_in_state: List[str] = ["network", "nodes", self.node_hostname, "applications", "WebBrowser"]
        web_browser_state = access_from_nested_dict(state, self.location_in_state)

        if web_browser_state is NOT_PRESENT_IN_STATE:
            self.reward = 0.0

        # check if the most recent action was to request the webpage
        request_attempted = last_action_response.request == [
            "network",
            "node",
            self._node,
            "application",
            "WebBrowser",
            "execute",
        ]

        # skip calculating if sticky and no new codes, reusing last step value
        if not request_attempted and self.sticky:
            return self.reward

        if last_action_response.response.status != "success":
            self.reward = -1.0
        elif web_browser_state is NOT_PRESENT_IN_STATE or not web_browser_state["history"]:
            _LOGGER.debug(
                "Web browser reward could not be calculated because the web browser history on node",
                f"{self._node} was not reported in the simulation state. Returning 0.0",
            )
            self.reward = 0.0
        else:
            outcome = web_browser_state["history"][-1]["outcome"]
            if outcome == "PENDING":
                self.reward = 0.0  # 0 if a request was attempted but not yet resolved
            elif outcome == 200:
                self.reward = 1.0  # 1 for successful request
            else:  # includes failure codes and SERVER_UNREACHABLE
                self.reward = -1.0  # -1 for failure

        return self.reward

    @classmethod
    def from_config(cls, config: dict) -> AbstractReward:
        """
        Build the reward component object from config.

        :param config: Configuration dictionary.
        :type config: Dict
        """
        node_hostname = config.get("node_hostname")
        sticky = config.get("sticky", True)
        return cls(node_hostname=node_hostname, sticky=sticky)


class GreenAdminDatabaseUnreachablePenalty(AbstractReward, identifier="GreenAdminDatabaseUnreachablePenalty"):
    """Penalises the agent when the green db clients fail to connect to the database."""
    node_hostname: str = ""
    _node: str = node_hostname
    sticky: bool = True
    reward: float = 0.0

    class ConfigSchema(AbstractReward.ConfigSchema):
        """ConfigSchema for GreenAdminDatabaseUnreachablePenalty."""

        node_hostname: str
        sticky: bool = True

    # def __init__(self, node_hostname: str, sticky: bool = True) -> None:
    #     """
    #     Initialise the reward component.

    #     :param node_hostname: Hostname of the node where the database client sits.
    #     :type node_hostname: str
    #     :param sticky: If True, calculate the reward based on the most recent response status. If False, only calculate
    #         the reward if there were any responses this timestep.
    #     :type sticky: bool
    #     """
    #     self._node: str = node_hostname
    #     self.location_in_state: List[str] = ["network", "nodes", node_hostname, "applications", "DatabaseClient"]
    #     self.sticky: bool = sticky
    #     self.reward: float = 0.0
    #     """Reward value calculated last time any responses were seen. Used for persisting sticky rewards."""

    def calculate(self, state: Dict, last_action_response: "AgentHistoryItem") -> float:
        """
        Calculate the reward based on current simulation state, and the recent agent action.

        When the green agent requests to execute the database client application, and that request fails, this reward
        component will keep track of that information. In that case, it doesn't matter whether the last successful
        request returned was able to connect to the database server, because there has been an unsuccessful request
        since.
        :param state: Current simulation state
        :type state: Dict
        :param last_action_response: Current agent history state
        :type last_action_response: AgentHistoryItem state
        :return: Reward value
        :rtype: float
        """
        request_attempted = last_action_response.request == [
            "network",
            "node",
            self._node,
            "application",
            "DatabaseClient",
            "execute",
        ]

        if request_attempted:  # if agent makes request, always recalculate fresh value
            last_action_response.reward_info = {"connection_attempt_status": last_action_response.response.status}
            self.reward = 1.0 if last_action_response.response.status == "success" else -1.0
        elif not self.sticky:  # if no new request and not sticky, set reward to 0
            last_action_response.reward_info = {"connection_attempt_status": "n/a"}
            self.reward = 0.0
        else:  # if no new request and sticky, reuse reward value from last step
            last_action_response.reward_info = {"connection_attempt_status": "n/a"}
            pass

        return self.reward

    @classmethod
    def from_config(cls, config: Dict) -> AbstractReward:
        """
        Build the reward component object from config.

        :param config: Configuration dictionary.
        :type config: Dict
        """
        node_hostname = config.get("node_hostname")
        sticky = config.get("sticky", True)
        return cls(node_hostname=node_hostname, sticky=sticky)


class SharedReward(AbstractReward, identifier="SharedReward"):
    """Adds another agent's reward to the overall reward."""
    agent_name: str

    class ConfigSchema(AbstractReward.ConfigSchema):
        """Config schema for SharedReward."""

        agent_name: str

    # def __init__(self, agent_name: Optional[str] = None) -> None:
    #     """
    #     Initialise the shared reward.

    #     The agent_name is a placeholder value. It starts off as none, but it must be set before this reward can work
    #     correctly.

    #     :param agent_name: The name whose reward is an input
    #     :type agent_name: Optional[str]
    #     """
    #     # self.agent_name = agent_name
    #     """Agent whose reward to track."""

    def default_callback(agent_name: str) -> Never:
        """
        Default callback to prevent calling this reward until it's properly initialised.

        SharedReward should not be used until the game layer replaces self.callback with a reference to the
        function that retrieves the desired agent's reward. Therefore, we define this default callback that raises
        an error.
        """
        raise RuntimeError("Attempted to calculate SharedReward but it was not initialised properly.")

    callback: Callable[[str], float] = default_callback
    """Method that retrieves an agent's current reward given the agent's name."""

    def calculate(self, state: Dict, last_action_response: "AgentHistoryItem") -> float:
        """Simply access the other agent's reward and return it.

        :param state: Current simulation state
        :type state: Dict
        :param last_action_response: Current agent history state
        :type last_action_response: AgentHistoryItem state
        :return: Reward value
        :rtype: float
        """
        return self.callback(self.agent_name)

    @classmethod
    def from_config(cls, config: Dict) -> "SharedReward":
        """
        Build the SharedReward object from config.

        :param config: Configuration dictionary
        :type config: Dict
        """
        agent_name = config.get("agent_name")
        return cls(agent_name=agent_name)


class ActionPenalty(AbstractReward, identifier="ActionPenalty"):
    """Apply a negative reward when taking any action except DONOTHING."""
    action_penalty: float = -1.0
    do_nothing_penalty: float = 0.0

    class ConfigSchema(AbstractReward.ConfigSchema):
        """Config schema for ActionPenalty."""

        action_penalty: float = -1.0
        do_nothing_penalty: float = 0.0

    # def __init__(self, action_penalty: float, do_nothing_penalty: float) -> None:
    #     """
    #     Initialise the reward.

    #     Reward or penalise agents for doing nothing or taking actions.

    #     :param action_penalty: Reward to give agents for taking any action except DONOTHING
    #     :type action_penalty: float
    #     :param do_nothing_penalty: Reward to give agent for taking the DONOTHING action
    #     :type do_nothing_penalty: float
    #     """
    #     super().__init__(action_penalty=action_penalty, do_nothing_penalty=do_nothing_penalty)
    #     self.action_penalty = action_penalty
    #     self.do_nothing_penalty = do_nothing_penalty

    def calculate(self, state: Dict, last_action_response: "AgentHistoryItem") -> float:
        """Calculate the penalty to be applied.

        :param state: Current simulation state
        :type state: Dict
        :param last_action_response: Current agent history state
        :type last_action_response: AgentHistoryItem state
        :return: Reward value
        :rtype: float
        """
        if last_action_response.action == "DONOTHING":
            return self.do_nothing_penalty
        else:
            return self.action_penalty

    @classmethod
    def from_config(cls, config: Dict) -> "ActionPenalty":
        """Build the ActionPenalty object from config."""
        action_penalty = config.get("action_penalty", -1.0)
        do_nothing_penalty = config.get("do_nothing_penalty", 0.0)
        return cls(action_penalty=action_penalty, do_nothing_penalty=do_nothing_penalty)


class RewardFunction:
    """Manages the reward function for the agent."""

    rew_class_identifiers: Dict[str, Type[AbstractReward]] = {
        "DUMMY": DummyReward,
        "DATABASE_FILE_INTEGRITY": DatabaseFileIntegrity,
        "WEB_SERVER_404_PENALTY": WebServer404Penalty,
        "WEBPAGE_UNAVAILABLE_PENALTY": WebpageUnavailablePenalty,
        "GREEN_ADMIN_DATABASE_UNREACHABLE_PENALTY": GreenAdminDatabaseUnreachablePenalty,
        "SHARED_REWARD": SharedReward,
        "ACTION_PENALTY": ActionPenalty,
    }
    """List of reward class identifiers."""

    def __init__(self):
        """Initialise the reward function object."""
        self.reward_components: List[Tuple[AbstractReward, float]] = []
        "attribute reward_components keeps track of reward components and the weights assigned to each."
        self.current_reward: float = 0.0
        self.total_reward: float = 0.0

    def register_component(self, component: AbstractReward, weight: float = 1.0) -> None:
        """Add a reward component to the reward function.

        :param component: Instance of a reward component.
        :type component: AbstractReward
        :param weight: Relative weight of the reward component, defaults to 1.0
        :type weight: float, optional
        """
        self.reward_components.append((component, weight))

    def update(self, state: Dict, last_action_response: "AgentHistoryItem") -> float:
        """Calculate the overall reward for the current state.

        :param state: The current state of the simulation.
        :type state: Dict
        """
        total = 0.0
        for comp_and_weight in self.reward_components:
            comp = comp_and_weight[0]
            weight = comp_and_weight[1]
            total += weight * comp.calculate(state=state, last_action_response=last_action_response)
        self.current_reward = total

        return self.current_reward

    @classmethod
    def from_config(cls, config: Dict) -> "RewardFunction":
        """Create a reward function from a config dictionary.

        :param config: dict of options for the reward manager's constructor
        :type config: Dict
        :return: The reward manager.
        :rtype: RewardFunction
        """
        new = cls()

        for rew_component_cfg in config["reward_components"]:
            rew_type = rew_component_cfg["type"]
            weight = rew_component_cfg.get("weight", 1.0)
            rew_class = cls.rew_class_identifiers[rew_type]
            rew_instance = rew_class.from_config(config=rew_component_cfg.get("options", {}))
            new.register_component(component=rew_instance, weight=weight)
        return new
