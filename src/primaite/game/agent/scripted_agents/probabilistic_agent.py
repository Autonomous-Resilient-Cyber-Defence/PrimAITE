# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
"""Agents with predefined behaviours."""
from typing import Dict, Optional, Tuple

import numpy as np
import pydantic
from gymnasium.core import ObsType

from primaite.game.agent.actions import ActionManager
from primaite.game.agent.interface import AbstractScriptedAgent
from primaite.game.agent.observations.observation_manager import ObservationManager
from primaite.game.agent.rewards import RewardFunction


class ProbabilisticAgent(AbstractScriptedAgent):
    """Scripted agent which randomly samples its action space with prescribed probabilities for each action."""

    class Settings(pydantic.BaseModel):
        """Config schema for Probabilistic agent settings."""

        model_config = pydantic.ConfigDict(extra="forbid")
        """Strict validation."""
        action_probabilities: Dict[int, float]
        """Probability to perform each action in the action map. The sum of probabilities should sum to 1."""
        # TODO: give the option to still set a random seed, but have it vary each episode in a predictable way
        #       for example if the user sets seed 123, have it be 123 + episode_num, so that each ep it's the next seed.

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

    def __init__(
        self,
        agent_name: str,
        action_space: Optional[ActionManager],
        observation_space: Optional[ObservationManager],
        reward_function: Optional[RewardFunction],
        settings: Dict = {},
    ) -> None:
        # If the action probabilities are not specified, create equal probabilities for all actions
        if "action_probabilities" not in settings:
            num_actions = len(action_space.action_map)
            settings = {"action_probabilities": {i: 1 / num_actions for i in range(num_actions)}}

        # The random number seed for np.random is dependent on whether a random number seed is set
        # in the config file. If there is one it is processed by set_random_seed() in environment.py
        # and as a consequence the the sequence of rng_seed's used here will be repeatable.
        self.settings = ProbabilisticAgent.Settings(**settings)
        rng_seed = np.random.randint(0, 65535)
        self.rng = np.random.default_rng(rng_seed)
        print(f"Probabilistic Agent - rng_seed: {rng_seed}")

        # convert probabilities from
        self.probabilities = np.asarray(list(self.settings.action_probabilities.values()))

        super().__init__(agent_name, action_space, observation_space, reward_function)
        self.logger.info(f"ProbabilisticAgent RNG seed: {rng_seed}")

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
