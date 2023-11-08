"""Interface for agents."""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, TypeAlias, Union

import numpy as np

from src.primaite.game.agent.actions import ActionManager
from src.primaite.game.agent.observations import ObservationSpace
from src.primaite.game.agent.rewards import RewardFunction

ObsType: TypeAlias = Union[Dict, np.ndarray]


class AbstractAgent(ABC):
    """Base class for scripted and RL agents."""

    def __init__(
        self,
        agent_name: Optional[str],
        action_space: Optional[ActionManager],
        observation_space: Optional[ObservationSpace],
        reward_function: Optional[RewardFunction],
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
        """
        self.agent_name: str = agent_name or "unnamed_agent"
        self.action_space: Optional[ActionManager] = action_space
        self.observation_space: Optional[ObservationSpace] = observation_space
        self.reward_function: Optional[RewardFunction] = reward_function

        # exection definiton converts CAOS action to Primaite simulator request, sometimes having to enrich the info
        # by for example specifying target ip addresses, or converting a node ID into a uuid
        self.execution_definition = None

    def convert_state_to_obs(self, state: Dict) -> ObsType:
        """
        Convert a state from the simulator into an observation for the agent using the observation space.

        state : dict state directly from simulation.describe_state
        output : dict state according to CAOS.
        """
        return self.observation_space.observe(state)

    def calculate_reward_from_state(self, state: Dict) -> float:
        """
        Use the reward function to calculate a reward from the state.

        :param state: State of the environment.
        :type state: Dict
        :return: Reward from the state.
        :rtype: float
        """
        return self.reward_function.calculate(state)

    @abstractmethod
    def get_action(self, obs: ObsType, reward: float = None) -> Tuple[str, Dict]:
        """
        Return an action to be taken in the environment.

        Subclasses should implement agent logic here. It should use the observation as input to decide best next action.

        :param obs: Observation of the environment.
        :type obs: ObsType
        :param reward: Reward from the previous action, defaults to None TODO: should this parameter even be accepted?
        :type reward: float, optional
        :return: Action to be taken in the environment.
        :rtype: Tuple[str, Dict]
        """
        # in RL agent, this method will send CAOS observation to GATE RL agent, then receive a int 0-39,
        # then use a bespoke conversion to take 1-40 int back into CAOS action
        return ("DO_NOTHING", {})

    def format_request(self, action: Tuple[str, Dict], options: Dict[str, int]) -> List[str]:
        # this will take something like APPLICATION.EXECUTE and add things like target_ip_address in simulator.
        # therefore the execution definition needs to be a mapping from CAOS into SIMULATOR
        """Format action into format expected by the simulator, and apply execution definition if applicable."""
        request = self.action_space.form_request(action_identifier=action, action_options=options)
        return request


class AbstractScriptedAgent(AbstractAgent):
    """Base class for actors which generate their own behaviour."""

    ...


class RandomAgent(AbstractScriptedAgent):
    """Agent that ignores its observation and acts completely at random."""

    def get_action(self, obs: ObsType, reward: float = None) -> Tuple[str, Dict]:
        """Randomly sample an action from the action space.

        :param obs: _description_
        :type obs: ObsType
        :param reward: _description_, defaults to None
        :type reward: float, optional
        :return: _description_
        :rtype: Tuple[str, Dict]
        """
        return self.action_space.get_action(self.action_space.space.sample())


class AbstractGATEAgent(AbstractAgent):
    """Base class for actors controlled via external messages, such as RL policies."""

    ...
