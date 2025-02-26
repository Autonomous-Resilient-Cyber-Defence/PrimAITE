# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
"""Interface for agents."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Dict, List, Literal, Optional, Tuple, Type, TYPE_CHECKING

from gymnasium.core import ActType, ObsType
from prettytable import PrettyTable
from pydantic import BaseModel, ConfigDict, Field

from primaite.game.agent.actions import ActionManager
from primaite.game.agent.agent_log import AgentLog
from primaite.game.agent.observations.observation_manager import ObservationManager
from primaite.game.agent.rewards import RewardFunction
from primaite.interface.request import RequestFormat, RequestResponse

if TYPE_CHECKING:
    pass

__all__ = ("AgentHistoryItem", "AbstractAgent", "AbstractScriptedAgent", "ProxyAgent")


class AgentHistoryItem(BaseModel):
    """One entry of an agent's action log - what the agent did and how the simulator responded in 1 step."""

    timestep: int
    """Timestep of this action."""

    action: str
    """CAOS Action name."""

    parameters: Dict[str, Any]
    """CAOS parameters for the given action."""

    request: RequestFormat
    """The request that was sent to the simulation based on the CAOS action chosen."""

    response: RequestResponse
    """The response sent back by the simulator for this action."""

    reward: Optional[float] = None

    reward_info: Dict[str, Any] = {}

    observation: Optional[ObsType] = None
    """The observation space data for this step."""


class AbstractAgent(BaseModel, ABC):
    """Base class for scripted and RL agents."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    class AgentSettingsSchema(BaseModel, ABC):
        """Schema for the 'agent_settings' key."""

        model_config = ConfigDict(extra="forbid")

    class ConfigSchema(BaseModel, ABC):
        """Configuration Schema for AbstractAgents."""

        model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)
        type: str
        ref: str = ""
        """name of the agent."""
        team: Optional[Literal["BLUE", "GREEN", "RED"]] = None
        agent_settings: AbstractAgent.AgentSettingsSchema = Field(default=lambda: AbstractAgent.AgentSettingsSchema())
        action_space: ActionManager.ConfigSchema = Field(default_factory=lambda: ActionManager.ConfigSchema())
        observation_space: ObservationManager.ConfigSchema = Field(
            default_factory=lambda: ObservationManager.ConfigSchema()
        )
        reward_function: RewardFunction.ConfigSchema = Field(default_factory=lambda: RewardFunction.ConfigSchema())
        thresholds: Optional[Dict] = {}
        # TODO: this is only relevant to some observations, need to refactor the way thresholds are dealt with (#3085)
        """A dict containing the observation thresholds."""

    config: ConfigSchema = Field(default_factory=lambda: AbstractAgent.ConfigSchema())

    logger: AgentLog = None
    history: List[AgentHistoryItem] = []

    action_manager: ActionManager = Field(default_factory=lambda: ActionManager())
    observation_manager: ObservationManager = Field(default_factory=lambda: ObservationManager())
    reward_function: RewardFunction = Field(default_factory=lambda: RewardFunction())

    _registry: ClassVar[Dict[str, Type[AbstractAgent]]] = {}

    def __init__(self, **kwargs):
        """Initialise and setup agent logger."""
        super().__init__(**kwargs)
        self.logger: AgentLog = AgentLog(agent_name=kwargs["config"]["ref"])

    def __init_subclass__(cls, discriminator: Optional[str] = None, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if discriminator is None:
            return
        if discriminator in cls._registry:
            raise ValueError(f"Cannot create a new agent under reserved name {discriminator}")
        cls._registry[discriminator] = cls

    def model_post_init(self, __context: Any) -> None:
        """Overwrite the default empty action, observation, and rewards with ones defined through the config."""
        self.action_manager = ActionManager(config=self.config.action_space)
        self.config.observation_space.options.thresholds = self.config.thresholds
        self.observation_manager = ObservationManager(config=self.config.observation_space)
        self.reward_function = RewardFunction(config=self.config.reward_function)
        return super().model_post_init(__context)

    def add_agent_action(self, item: AgentHistoryItem, table: PrettyTable) -> PrettyTable:
        """Update the given table with information from given AgentHistoryItem."""
        node, application = "unknown", "unknown"
        if (node_id := item.parameters.get("node_id")) is not None:
            node = self.action_manager.node_names[node_id]
        if (application_id := item.parameters.get("application_id")) is not None:
            application = self.action_manager.application_names[node_id][application_id]
        if (application_name := item.parameters.get("application_name")) is not None:
            application = application_name
        table.add_row([item.timestep, item.action, node, application, item.response.status])
        return table

    def show_history(self, ignored_actions: Optional[list] = None):
        """
        Print an agent action provided it's not the DONOTHING action.

        :param ignored_actions: OPTIONAL: List of actions to be ignored when displaying the history.
                                If not provided, defaults to ignore DONOTHING actions.
        """
        if not ignored_actions:
            ignored_actions = ["DONOTHING"]
        table = PrettyTable()
        table.field_names = ["Step", "Action", "Node", "Application", "Response"]
        print(f"Actions for '{self.agent_name}':")
        for item in self.history:
            if item.action in ignored_actions:
                pass
            else:
                table = self.add_agent_action(item=item, table=table)
        print(table)

    def update_observation(self, state: Dict) -> ObsType:
        """
        Convert a state from the simulator into an observation for the agent using the observation space.

        state : dict state directly from simulation.describe_state
        output : dict state according to CAOS.
        """
        return self.observation_manager.update(state)

    def update_reward(self, state: Dict) -> float:
        """
        Use the reward function to calculate a reward from the state.

        :param state: State of the environment.
        :type state: Dict
        :return: Reward from the state.
        :rtype: float
        """
        return self.reward_function.update(state=state, last_action_response=self.history[-1])

    @abstractmethod
    def get_action(self, obs: ObsType, timestep: int = 0) -> Tuple[str, Dict]:
        """
        Return an action to be taken in the environment.

        Subclasses should implement agent logic here. It should use the observation as input to decide best next action.

        :param obs: Observation of the environment.
        :type obs: ObsType
        :param timestep: The current timestep in the simulation, used for non-RL agents. Optional
        :type timestep: int
        :return: Action to be taken in the environment.
        :rtype: Tuple[str, Dict]
        """
        # in RL agent, this method will send CAOS observation to RL agent, then receive a int 0-39,
        # then use a bespoke conversion to take 1-40 int back into CAOS action
        return ("do-nothing", {})

    def format_request(self, action: Tuple[str, Dict], options: Dict[str, int]) -> RequestFormat:
        # this will take something like APPLICATION.EXECUTE and add things like target_ip_address in simulator.
        # therefore the execution definition needs to be a mapping from CAOS into SIMULATOR
        """Format action into format expected by the simulator, and apply execution definition if applicable."""
        request = self.action_manager.form_request(action_identifier=action, action_options=options)
        return request

    def process_action_response(
        self,
        timestep: int,
        action: str,
        parameters: Dict[str, Any],
        request: RequestFormat,
        response: RequestResponse,
        observation: ObsType,
    ) -> None:
        """Process the response from the most recent action."""
        self.history.append(
            AgentHistoryItem(
                timestep=timestep,
                action=action,
                parameters=parameters,
                request=request,
                response=response,
                observation=observation,
            )
        )

    def save_reward_to_history(self) -> None:
        """Update the most recent history item with the reward value."""
        self.history[-1].reward = self.reward_function.current_reward

    @classmethod
    def from_config(cls, config: Dict) -> AbstractAgent:
        """Grab the relevant agent class and construct an instance from a config dict."""
        agent_type = config["type"]
        agent_class = cls._registry[agent_type]
        return agent_class(config=config)


class AbstractScriptedAgent(AbstractAgent, ABC):
    """Base class for actors which generate their own behaviour."""

    class ConfigSchema(AbstractAgent.ConfigSchema, ABC):
        """Configuration Schema for AbstractScriptedAgents."""

        type: str = "AbstractScriptedAgent"

    config: ConfigSchema = Field(default_factory=lambda: AbstractScriptedAgent.ConfigSchema())

    @abstractmethod
    def get_action(self, obs: ObsType, timestep: int = 0) -> Tuple[str, Dict]:
        """Return an action to be taken in the environment."""
        return super().get_action(obs=obs, timestep=timestep)


class ProxyAgent(AbstractAgent, discriminator="proxy-agent"):
    """Agent that sends observations to an RL model and receives actions from that model."""

    config: "ProxyAgent.ConfigSchema" = Field(default_factory=lambda: ProxyAgent.ConfigSchema())
    most_recent_action: ActType = None

    class AgentSettingsSchema(AbstractAgent.AgentSettingsSchema):
        """Schema for the `agent_settings` part of the agent config."""

        flatten_obs: bool = False
        action_masking: bool = False

    class ConfigSchema(AbstractAgent.ConfigSchema):
        """Configuration Schema for Proxy Agent."""

        type: str = "Proxy_Agent"
        agent_settings: ProxyAgent.AgentSettingsSchema = Field(default_factory=lambda: ProxyAgent.AgentSettingsSchema())

    def get_action(self, obs: ObsType, timestep: int = 0) -> Tuple[str, Dict]:
        """
        Return the agent's most recent action, formatted in CAOS format.

        :param obs: Observation for the agent. Not used by ProxyAgents, but required by the interface.
        :type obs: ObsType
        :param timestep: Current simulation timestep. Not used by ProxyAgents, bur required for the interface.
        :type timestep: int
        :return: Action to be taken in CAOS format.
        :rtype: Tuple[str, Dict]
        """
        return self.action_manager.get_action(self.most_recent_action)

    def store_action(self, action: ActType):
        """
        Store the most recent action taken by the agent.

        The environment is responsible for calling this method when it receives an action from the agent policy.
        """
        self.most_recent_action = action

    @property
    def flatten_obs(self) -> bool:
        """Return agent flatten_obs param."""
        return self.config.agent_settings.flatten_obs
