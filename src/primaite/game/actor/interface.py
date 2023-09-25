# TODO: remove this comment... This is just here to point out that I've named this 'actor' rather than 'agent'
# That's because I want to point out that this is disctinct from 'agent' in the reinforcement learning sense of the word
# If you disagree, make a comment in the PR review and we can discuss
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from pydantic import BaseModel

from primaite.game.actor.actions import ActionSpace
from primaite.game.actor.observations import ObservationSpace
from primaite.game.actor.rewards import RewardFunction


class AbstractActor(ABC):
    """Base class for scripted and RL agents."""

    def __init__(self) -> None:
        self.action_space = ActionSpace
        self.observation_space = ObservationSpace
        self.reward_function = RewardFunction


class AbstractScriptedActor(AbstractActor):
    """Base class for actors which generate their own behaviour."""

    ...


class AbstractPuppetActor(AbstractActor):
    """Base class for actors controlled via external messages, such as RL policies."""

    ...


# class AbstractRLActor(AbstractPuppetActor): ??
