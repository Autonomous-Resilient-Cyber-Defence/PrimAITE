# TODO: remove this comment... This is just here to point out that I've named this 'actor' rather than 'agent'
# That's because I want to point out that this is disctinct from 'agent' in the reinforcement learning sense of the word
# If you disagree, make a comment in the PR review and we can discuss
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, TypeAlias, Union

import numpy as np

from primaite.game.agent.actions import ActionManager
from primaite.game.agent.observations import ObservationSpace
from primaite.game.agent.rewards import RewardFunction

ObsType: TypeAlias = Union[Dict, np.ndarray]


class AbstractAgent(ABC):
    """Base class for scripted and RL agents."""

    def __init__(
        self,
        action_space: Optional[ActionManager],
        observation_space: Optional[ObservationSpace],
        reward_function: Optional[RewardFunction],
    ) -> None:
        self.action_space: Optional[ActionManager] = action_space
        self.observation_space: Optional[ObservationSpace] = observation_space
        self.reward_function: Optional[RewardFunction] = reward_function

        # exection definiton converts CAOS action to Primaite simulator request, sometimes having to enrich the info
        # by for example specifying target ip addresses, or converting a node ID into a uuid
        self.execution_definition = None

    def convert_state_to_obs(self, state: Dict) -> ObsType:
        """
        state : dict state directly from simulation.describe_state
        output : dict state according to CAOS.
        """
        return self.observation_space.observe(state)

    def calculate_reward_from_state(self, state: Dict) -> float:
        return self.reward_function.calculate(state)

    @abstractmethod
    def get_action(self, obs: ObsType, reward: float = None) -> Tuple[str, Dict]:
        # in RL agent, this method will send CAOS observation to GATE RL agent, then receive a int 0-39,
        # then use a bespoke conversion to take 1-40 int back into CAOS action
        return ("DO_NOTHING", {} )

    def format_request(self, action:Tuple[str,Dict], options:Dict[str, int]) -> List[str]:
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
        return self.action_space.get_action(self.action_space.space.sample())


class AbstractGATEAgent(AbstractAgent):
    """Base class for actors controlled via external messages, such as RL policies."""

    ...
