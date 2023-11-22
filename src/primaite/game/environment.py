from typing import Any, Dict, List, Optional, SupportsFloat, Tuple

import gymnasium
from gymnasium.core import ActType, ObsType

from primaite.game.agent.interface import ProxyAgent
from primaite.game.game import PrimaiteGame


class PrimaiteGymEnv(gymnasium.Env):
    """
    Thin wrapper env to provide agents with a gymnasium API.

    This is always a single agent environment since gymnasium is a single agent API. Therefore, we can make some
    assumptions about the agent list always having a list of length 1.
    """

    def __init__(self, game: PrimaiteGame, agents: List[ProxyAgent]):
        """Initialise the environment."""
        super().__init__()
        self.game: "PrimaiteGame" = game
        self.agent: ProxyAgent = agents[0]

    def step(self, action: ActType) -> Tuple[ObsType, SupportsFloat, bool, bool, Dict[str, Any]]:
        """Perform a step in the environment."""
        # make ProxyAgent store the action chosen my the RL policy
        self.agent.store_action(action)
        # apply_agent_actions accesses the action we just stored
        self.game.apply_agent_actions()
        self.game.advance_timestep()
        state = self.game.get_sim_state()
        self.game.update_agents(state)

        next_obs = self._get_obs()
        reward = self.agent.reward_function.current_reward
        terminated = False
        truncated = self.game.calculate_truncated()
        info = {}

        return next_obs, reward, terminated, truncated, info

    def reset(self, seed: Optional[int] = None) -> Tuple[ObsType, Dict[str, Any]]:
        """Reset the environment."""
        self.game.reset()
        state = self.game.get_sim_state()
        self.game.update_agents(state)
        next_obs = self._get_obs()
        info = {}
        return next_obs, info

    @property
    def action_space(self) -> gymnasium.Space:
        """Return the action space of the environment."""
        return self.agent.action_manager.space

    @property
    def observation_space(self) -> gymnasium.Space:
        """Return the observation space of the environment."""
        return gymnasium.spaces.flatten_space(self.agent.observation_manager.space)

    def _get_obs(self) -> ObsType:
        """Return the current observation."""
        unflat_space = self.agent.observation_manager.space
        unflat_obs = self.agent.observation_manager.current_observation
        return gymnasium.spaces.flatten(unflat_space, unflat_obs)
