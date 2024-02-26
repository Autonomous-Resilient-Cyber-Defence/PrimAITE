"""Agents with predefined behaviours."""
from typing import Dict, Optional, Tuple

import numpy as np
import pydantic
from gymnasium.core import ObsType

from primaite.game.agent.actions import ActionManager
from primaite.game.agent.interface import AbstractScriptedAgent
from primaite.game.agent.observations import ObservationManager
from primaite.game.agent.rewards import RewardFunction


class GreenUC2Agent(AbstractScriptedAgent):
    """Scripted agent which attempts to send web requests to a target node."""

    class GreenUC2AgentSettings(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(extra="forbid")
        action_probabilities: Dict[int, float]
        """Probability to perform each action in the action map. The sum of probabilities should sum to 1."""
        random_seed: Optional[int] = None

        @pydantic.field_validator("action_probabilities", mode="after")
        @classmethod
        def probabilities_sum_to_one(cls, v: Dict[int, float]) -> Dict[int, float]:
            if not abs(sum(v.values()) - 1) < 1e-6:
                raise ValueError(f"Green action probabilities must sum to 1")
            return v

        @pydantic.field_validator("action_probabilities", mode="after")
        @classmethod
        def action_map_covered_correctly(cls, v: Dict[int, float]) -> Dict[int, float]:
            if not all((i in v) for i in range(len(v))):
                raise ValueError(
                    "Green action probabilities must be defined as a mapping where the keys are consecutive integers "
                    "from 0 to N."
                )

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

        # If seed not specified, set it to None so that numpy chooses a random one.
        settings.setdefault("random_seed")

        self.settings = GreenUC2Agent.GreenUC2AgentSettings(settings)

        self.rng = np.random.default_rng(self.settings.random_seed)

        # convert probabilities from
        self.probabilities = np.array[self.settings.action_probabilities.values()]

        super().__init__(agent_name, action_space, observation_space, reward_function)

    def get_action(self, obs: ObsType, reward: float = 0) -> Tuple[str, Dict]:
        choice = self.rng.choice(len(self.action_manager.action_map), p=self.probabilities)
        return self.action_manager.get_action(choice)

    raise NotImplementedError


class RedDatabaseCorruptingAgent(AbstractScriptedAgent):
    """Scripted agent which attempts to corrupt the database of the target node."""

    raise NotImplementedError
