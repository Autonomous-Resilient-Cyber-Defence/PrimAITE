# TODO: remove this comment... This is just here to point out that I've named this 'actor' rather than 'agent'
# That's because I want to point out that this is disctinct from 'agent' in the reinforcement learning sense of the word
# If you disagree, make a comment in the PR review and we can discuss
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from primaite.game.agent.actions import ActionSpace
from primaite.game.agent.observations import ObservationSpace
from primaite.game.agent.rewards import RewardFunction


class AbstractAgent(ABC):
    """Base class for scripted and RL agents."""

    def __init__(
        self,
        action_space: Optional[ActionSpace],
        observation_space: Optional[ObservationSpace],
        reward_function: Optional[RewardFunction],
    ) -> None:
        self.action_space: Optional[ActionSpace] = action_space
        self.observation_space: Optional[ObservationSpace] = observation_space
        self.reward_function: Optional[RewardFunction] = reward_function


class AbstractScriptedAgent(AbstractAgent):
    """Base class for actors which generate their own behaviour."""

    ...


class AbstractGATEAgent(AbstractAgent):
    """Base class for actors controlled via external messages, such as RL policies."""

    ...
