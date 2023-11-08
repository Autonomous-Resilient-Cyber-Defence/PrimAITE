# flake8: noqa
from typing import Dict, Optional, Tuple

from gymnasium.core import ActType, ObsType

from src.primaite.game.agent.actions import ActionManager
from src.primaite.game.agent.interface import AbstractGATEAgent, ObsType
from src.primaite.game.agent.observations import ObservationSpace
from src.primaite.game.agent.rewards import RewardFunction


class GATERLAgent(AbstractGATEAgent):
    ...
    # The communication with GATE needs to be handled by the PrimaiteSession, rather than by individual agents,
    # because when we are supporting MARL, the actions form multiple agents will have to be batched

    # For example MultiAgentEnv in Ray allows sending a dict of observations of multiple agents, then it will reply
    # with the actions for those agents.

    def __init__(
        self,
        agent_name: str | None,
        action_space: ActionManager | None,
        observation_space: ObservationSpace | None,
        reward_function: RewardFunction | None,
    ) -> None:
        super().__init__(agent_name, action_space, observation_space, reward_function)
        self.most_recent_action: ActType

    def get_action(self, obs: ObsType, reward: float = None) -> Tuple[str, Dict]:
        return self.most_recent_action
