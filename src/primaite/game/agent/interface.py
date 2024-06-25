# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
"""Interface for agents."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from gymnasium.core import ActType, ObsType
from pydantic import BaseModel, model_validator

from primaite.game.agent.actions import ActionManager
from primaite.game.agent.observations.observation_manager import ObservationManager
from primaite.game.agent.rewards import RewardFunction
from primaite.interface.request import RequestFormat, RequestResponse

if TYPE_CHECKING:
    pass


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


class AgentStartSettings(BaseModel):
    """Configuration values for when an agent starts performing actions."""

    start_step: int = 5
    "The timestep at which an agent begins performing it's actions"
    frequency: int = 5
    "The number of timesteps to wait between performing actions"
    variance: int = 0
    "The amount the frequency can randomly change to"

    @model_validator(mode="after")
    def check_variance_lt_frequency(self) -> "AgentStartSettings":
        """
        Make sure variance is equal to or lower than frequency.

        This is because the calculation for the next execution time is now + (frequency +- variance). If variance were
        greater than frequency, sometimes the bracketed term would be negative and the attack would never happen again.
        """
        if self.variance > self.frequency:
            raise ValueError(
                f"Agent start settings error: variance must be lower than frequency "
                f"{self.variance=}, {self.frequency=}"
            )
        return self


class AgentSettings(BaseModel):
    """Settings for configuring the operation of an agent."""

    start_settings: Optional[AgentStartSettings] = None
    "Configuration for when an agent begins performing it's actions"
    flatten_obs: bool = True
    "Whether to flatten the observation space before passing it to the agent. True by default."

    @classmethod
    def from_config(cls, config: Optional[Dict]) -> "AgentSettings":
        """Construct agent settings from a config dictionary.

        :param config: A dict of options for the agent settings.
        :type config: Dict
        :return: The agent settings.
        :rtype: AgentSettings
        """
        if config is None:
            return cls()

        return cls(**config)


class AbstractAgent(ABC):
    """Base class for scripted and RL agents."""

    def __init__(
        self,
        agent_name: Optional[str],
        action_space: Optional[ActionManager],
        observation_space: Optional[ObservationManager],
        reward_function: Optional[RewardFunction],
        agent_settings: Optional[AgentSettings] = None,
    ) -> None:
        """
        Initialize an agent.

        :param agent_name: Unique string identifier for the agent, for reporting and multi-agent purposes.
        :type agent_name: Optional[str]
        :param action_space: Action space for the agent.
        :type action_space: Optional[ActionManager]
        :param observation_space: Observation space for the agent.
        :type observation_space: Optional[ObservationSpace]
        :param reward_function: Reward function for the agent.
        :type reward_function: Optional[RewardFunction]
        :param agent_settings: Configurable Options for Abstracted Agents
        :type agent_settings: Optional[AgentSettings]
        """
        self.agent_name: str = agent_name or "unnamed_agent"
        self.action_manager: Optional[ActionManager] = action_space
        self.observation_manager: Optional[ObservationManager] = observation_space
        self.reward_function: Optional[RewardFunction] = reward_function
        self.agent_settings = agent_settings or AgentSettings()
        self.history: List[AgentHistoryItem] = []

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
        return ("DO_NOTHING", {})

    def format_request(self, action: Tuple[str, Dict], options: Dict[str, int]) -> List[str]:
        # this will take something like APPLICATION.EXECUTE and add things like target_ip_address in simulator.
        # therefore the execution definition needs to be a mapping from CAOS into SIMULATOR
        """Format action into format expected by the simulator, and apply execution definition if applicable."""
        request = self.action_manager.form_request(action_identifier=action, action_options=options)
        return request

    def process_action_response(
        self, timestep: int, action: str, parameters: Dict[str, Any], request: RequestFormat, response: RequestResponse
    ) -> None:
        """Process the response from the most recent action."""
        self.history.append(
            AgentHistoryItem(
                timestep=timestep, action=action, parameters=parameters, request=request, response=response
            )
        )

    def save_reward_to_history(self) -> None:
        """Update the most recent history item with the reward value."""
        self.history[-1].reward = self.reward_function.current_reward


class AbstractScriptedAgent(AbstractAgent):
    """Base class for actors which generate their own behaviour."""

    @abstractmethod
    def get_action(self, obs: ObsType, timestep: int = 0) -> Tuple[str, Dict]:
        """Return an action to be taken in the environment."""
        return super().get_action(obs=obs, timestep=timestep)


class ProxyAgent(AbstractAgent):
    """Agent that sends observations to an RL model and receives actions from that model."""

    def __init__(
        self,
        agent_name: Optional[str],
        action_space: Optional[ActionManager],
        observation_space: Optional[ObservationManager],
        reward_function: Optional[RewardFunction],
        agent_settings: Optional[AgentSettings] = None,
    ) -> None:
        super().__init__(
            agent_name=agent_name,
            action_space=action_space,
            observation_space=observation_space,
            reward_function=reward_function,
        )
        self.most_recent_action: ActType
        self.flatten_obs: bool = agent_settings.flatten_obs if agent_settings else False

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
