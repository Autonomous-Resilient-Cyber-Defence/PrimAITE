# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
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
            - type: database-file-integrity
            weight: 0.5
            options:
                node_name: database_server
                folder_name: database
                file_name: database.db


            - type: web-server-404-penalty
            weight: 0.5
            options:
                node_name: web_server
                service_ref: web_server_database_client
```
"""
from abc import ABC, abstractmethod
from typing import Any, Callable, ClassVar, Dict, Iterable, List, Optional, Tuple, Type, TYPE_CHECKING, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing_extensions import Never

from primaite import getLogger
from primaite.game.agent.utils import access_from_nested_dict, NOT_PRESENT_IN_STATE

if TYPE_CHECKING:
    from primaite.game.agent.interface import AgentHistoryItem

_LOGGER = getLogger(__name__)
WhereType = Optional[Iterable[Union[str, int]]]


class AbstractReward(BaseModel, ABC):
    """Base class for reward function components."""

    class ConfigSchema(BaseModel, ABC):
        """Config schema for AbstractReward."""

        type: str = ""

    config: ConfigSchema

    _registry: ClassVar[Dict[str, Type["AbstractReward"]]] = {}

    def __init_subclass__(cls, discriminator: Optional[str] = None, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if discriminator is None:
            return
        if discriminator in cls._registry:
            raise ValueError(f"Duplicate reward {discriminator}")
        cls._registry[discriminator] = cls

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
        reward_class = cls._registry[config["type"]]
        reward_obj = reward_class(config=reward_class.ConfigSchema(**config))
        return reward_obj

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


class DummyReward(AbstractReward, discriminator="dummy"):
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


class DatabaseFileIntegrity(AbstractReward, discriminator="database-file-integrity"):
    """Reward function component which rewards the agent for maintaining the integrity of a database file."""

    config: "DatabaseFileIntegrity.ConfigSchema"
    location_in_state: List[str] = [""]
    reward: float = 0.0

    class ConfigSchema(AbstractReward.ConfigSchema):
        """ConfigSchema for DatabaseFileIntegrity."""

        type: str = "database-file-integrity"
        node_hostname: str
        folder_name: str
        file_name: str

    def calculate(self, state: Dict, last_action_response: "AgentHistoryItem") -> float:
        """Calculate the reward for the current state.

        :param state: Current simulation state
        :type state: Dict
        :param last_action_response: Current agent history state
        :type last_action_response: AgentHistoryItem state
        :return: Reward value
        :rtype: float
        """
        self.location_in_state = [
            "network",
            "nodes",
            self.config.node_hostname,
            "file_system",
            "folders",
            self.config.folder_name,
            "files",
            self.config.file_name,
        ]

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


class WebServer404Penalty(AbstractReward, discriminator="web-server-404-penalty"):
    """Reward function component which penalises the agent when the web server returns a 404 error."""

    config: "WebServer404Penalty.ConfigSchema"
    location_in_state: List[str] = [""]
    reward: float = 0.0

    class ConfigSchema(AbstractReward.ConfigSchema):
        """ConfigSchema for WebServer404Penalty."""

        type: str = "web-server-404-penalty"
        node_hostname: str
        service_name: str
        sticky: bool = True

    def calculate(self, state: Dict, last_action_response: "AgentHistoryItem") -> float:
        """Calculate the reward for the current state.

        :param state: Current simulation state
        :type state: Dict
        :param last_action_response: Current agent history state
        :type last_action_response: AgentHistoryItem state
        :return: Reward value
        :rtype: float
        """
        self.location_in_state = [
            "network",
            "nodes",
            self.config.node_hostname,
            "services",
            self.config.service_name,
        ]
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
        elif not self.config.sticky:  # there are no codes, but reward is not sticky, set reward to 0
            self.reward = 0.0
        else:  # skip calculating if sticky and no new codes. instead, reuse last step's value
            pass

        return self.reward


class WebpageUnavailablePenalty(AbstractReward, discriminator="webpage-unavailable-penalty"):
    """Penalises the agent when the web browser fails to fetch a webpage."""

    config: "WebpageUnavailablePenalty.ConfigSchema"
    reward: float = 0.0
    location_in_state: List[str] = [""]  # Calculate in __init__()?

    class ConfigSchema(AbstractReward.ConfigSchema):
        """ConfigSchema for WebpageUnavailablePenalty."""

        type: str = "webpage-unavailable-penalty"
        node_hostname: str = ""
        sticky: bool = True

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
        self.location_in_state = [
            "network",
            "nodes",
            self.config.node_hostname,
            "applications",
            "web-browser",
        ]
        web_browser_state = access_from_nested_dict(state, self.location_in_state)

        if web_browser_state is NOT_PRESENT_IN_STATE:
            self.reward = 0.0

        # check if the most recent action was to request the webpage
        request_attempted = last_action_response.request == [
            "network",
            "node",
            self.config.node_hostname,
            "application",
            "web-browser",
            "execute",
        ]

        # skip calculating if sticky and no new codes, reusing last step value
        if not request_attempted and self.config.sticky:
            return self.reward

        if last_action_response.response.status != "success":
            self.reward = -1.0
        elif web_browser_state is NOT_PRESENT_IN_STATE or not web_browser_state["history"]:
            _LOGGER.debug(
                "Web browser reward could not be calculated because the web browser history on node",
                f"{self.config.node_hostname} was not reported in the simulation state. Returning 0.0",
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


class GreenAdminDatabaseUnreachablePenalty(AbstractReward, discriminator="green-admin-database-unreachable-penalty"):
    """Penalises the agent when the green db clients fail to connect to the database."""

    config: "GreenAdminDatabaseUnreachablePenalty.ConfigSchema"
    reward: float = 0.0

    class ConfigSchema(AbstractReward.ConfigSchema):
        """ConfigSchema for GreenAdminDatabaseUnreachablePenalty."""

        type: str = "green-admin-database-unreachable-penalty"
        node_hostname: str
        sticky: bool = True

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
            self.config.node_hostname,
            "application",
            "database-client",
            "execute",
        ]

        if request_attempted:  # if agent makes request, always recalculate fresh value
            last_action_response.reward_info = {"connection_attempt_status": last_action_response.response.status}
            self.reward = 1.0 if last_action_response.response.status == "success" else -1.0
        elif not self.config.sticky:  # if no new request and not sticky, set reward to 0
            last_action_response.reward_info = {"connection_attempt_status": "n/a"}
            self.reward = 0.0
        else:  # if no new request and sticky, reuse reward value from last step
            last_action_response.reward_info = {"connection_attempt_status": "n/a"}
            pass

        return self.reward


class SharedReward(AbstractReward, discriminator="shared-reward"):
    """Adds another agent's reward to the overall reward."""

    config: "SharedReward.ConfigSchema"

    class ConfigSchema(AbstractReward.ConfigSchema):
        """Config schema for SharedReward."""

        type: str = "shared-reward"
        agent_name: str

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
        return self.callback(self.config.agent_name)


class ActionPenalty(AbstractReward, discriminator="action-penalty"):
    """Apply a negative reward when taking any action except do-nothing."""

    config: "ActionPenalty.ConfigSchema"

    class ConfigSchema(AbstractReward.ConfigSchema):
        """Config schema for ActionPenalty.

        :param action_penalty: Reward to give agents for taking any action except do-nothing
        :type action_penalty: float
        :param do_nothing_penalty: Reward to give agent for taking the do-nothing action
        :type do_nothing_penalty: float
        """

        action_penalty: float = -1.0
        do_nothing_penalty: float = 0.0

    def calculate(self, state: Dict, last_action_response: "AgentHistoryItem") -> float:
        """Calculate the penalty to be applied.

        :param state: Current simulation state
        :type state: Dict
        :param last_action_response: Current agent history state
        :type last_action_response: AgentHistoryItem state
        :return: Reward value
        :rtype: float
        """
        if last_action_response.action == "do-nothing":
            return self.config.do_nothing_penalty

        else:
            return self.config.action_penalty


class _SingleComponentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: str
    options: AbstractReward.ConfigSchema
    weight: float = 1.0

    @model_validator(mode="before")
    @classmethod
    def resolve_obs_options_type(cls, data: Any) -> Any:
        """
        When constructing the model from a dict, resolve the correct reward class based on `type` field.

        Workaround: The `options` field is statically typed as AbstractReward. Therefore, it falls over when
        passing in data that adheres to a subclass schema rather than the plain AbstractReward schema. There is
        a way to do this properly using discriminated union, but most advice on the internet assumes that the full
        list of types between which to discriminate is known ahead-of-time. That is not the case for us, because of
        our plugin architecture.

        We may be able to revisit and implement a better solution when needed using the following resources as
        research starting points:
        https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions
        https://github.com/pydantic/pydantic/issues/7366
        https://github.com/pydantic/pydantic/issues/7462
        https://github.com/pydantic/pydantic/pull/7983
        """
        if not isinstance(data, dict):
            return data

        assert "type" in data, ValueError('Reward component definition is missing the "type" key.')
        rew_type = data["type"]
        rew_class = AbstractReward._registry[rew_type]

        # if no options are passed in, try to create a default schema. Only works if there are no mandatory fields.
        if "options" not in data:
            data["options"] = rew_class.ConfigSchema()

        # if options are passed as a dict, validate against schema
        elif isinstance(data["options"], dict):
            data["options"] = rew_class.ConfigSchema(**data["options"])

        return data


class RewardFunction(BaseModel):
    """Manages the reward function for the agent."""

    model_config = ConfigDict(extra="forbid")

    class ConfigSchema(BaseModel):
        """Config Schema for RewardFunction."""

        model_config = ConfigDict(extra="forbid")

        reward_components: Iterable[_SingleComponentConfig] = []

    config: ConfigSchema = Field(default_factory=lambda: RewardFunction.ConfigSchema())

    reward_components: List[Tuple[AbstractReward, float]] = []

    current_reward: float = 0.0
    total_reward: float = 0.0

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        for rew_config in self.config.reward_components:
            rew_class = AbstractReward._registry[rew_config.type]
            rew_instance = rew_class(config=rew_config.options)
            self.register_component(component=rew_instance, weight=rew_config.weight)

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
        """Create a reward function from a config dictionary and its related reward class.

        :param config: dict of options for the reward manager's constructor
        :type config: Dict
        :return: The reward manager.
        :rtype: RewardFunction
        """
        new = cls()

        for rew_component_cfg in config["reward_components"]:
            rew_type = rew_component_cfg["type"]
            # XXX: If options key is missing add key then add type key.
            if "options" not in rew_component_cfg:
                rew_component_cfg["options"] = {}
            rew_component_cfg["options"]["type"] = rew_type
            weight = rew_component_cfg.get("weight", 1.0)
            rew_instance = AbstractReward.from_config(rew_component_cfg["options"])
            new.register_component(component=rew_instance, weight=weight)
        return new
