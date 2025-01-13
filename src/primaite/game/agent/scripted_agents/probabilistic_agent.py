# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
"""Agents with predefined behaviours."""
from typing import Dict, Tuple

import numpy as np
import pydantic
from gymnasium.core import ObsType
from numpy.random import Generator
from pydantic import Field

from primaite.game.agent.interface import AbstractScriptedAgent

__all__ = "ProbabilisticAgent"


class ProbabilisticAgent(AbstractScriptedAgent, identifier="ProbabilisticAgent"):
    """Scripted agent which randomly samples its action space with prescribed probabilities for each action."""

    config: "ProbabilisticAgent.ConfigSchema" = Field(default_factory=lambda: ProbabilisticAgent.ConfigSchema())
    rng: Generator = np.random.default_rng(np.random.randint(0, 65535))

    class ConfigSchema(AbstractScriptedAgent.ConfigSchema):
        """Configuration schema for Probabilistic Agent."""

        type: str = "ProbabilisticAgent"

        action_probabilities: Dict[int, float] = None
        """Probability to perform each action in the action map. The sum of probabilities should sum to 1."""

        @pydantic.field_validator("action_probabilities", mode="after")
        @classmethod
        def probabilities_sum_to_one(cls, v: Dict[int, float]) -> Dict[int, float]:
            """Make sure the probabilities sum to 1."""
            if not abs(sum(v.values()) - 1) < 1e-6:
                raise ValueError("Green action probabilities must sum to 1")
            return v

        @pydantic.field_validator("action_probabilities", mode="after")
        @classmethod
        def action_map_covered_correctly(cls, v: Dict[int, float]) -> Dict[int, float]:
            """Ensure that the keys of the probability dictionary cover all integers from 0 to N."""
            if not all((i in v) for i in range(len(v))):
                raise ValueError(
                    "Green action probabilities must be defined as a mapping where the keys are consecutive integers "
                    "from 0 to N."
                )
            return v

    @property
    def probabilities(self) -> Dict[str, int]:
        """Convenience method to view the probabilities of the Agent."""
        return np.asarray(list(self.config.action_probabilities.values()))

    def get_action(self, obs: ObsType, timestep: int = 0) -> Tuple[str, Dict]:
        """
        Sample the action space randomly.

        The probability of each action is given by the corresponding index in ``self.probabilities``.

        :param obs: Current observation for this agent, not used in ProbabilisticAgent
        :type obs: ObsType
        :param timestep: The current simulation timestep, not used in ProbabilisticAgent
        :type timestep: int
        :return: Action formatted in CAOS format
        :rtype: Tuple[str, Dict]
        """
        choice = self.rng.choice(len(self.action_manager.action_map), p=self.probabilities)
        self.logger.info(f"Performing Action: {choice}")
        return self.action_manager.get_action(choice)
