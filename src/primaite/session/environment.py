# import os
from typing import Any, Dict, Final, Optional, SupportsFloat, Tuple

import gymnasium
from gymnasium.core import ActType, ObsType
from ray.rllib.env.multi_agent_env import MultiAgentEnv

from primaite import PRIMAITE_PATHS
from primaite.game.agent.interface import ProxyAgent
from primaite.game.game import PrimaiteGame


class PrimaiteGymEnv(gymnasium.Env):
    """
    Thin wrapper env to provide agents with a gymnasium API.

    This is always a single agent environment since gymnasium is a single agent API. Therefore, we can make some
    assumptions about the agent list always having a list of length 1.
    """

    def __init__(self, game: PrimaiteGame):
        """Initialise the environment."""
        super().__init__()
        self.game: "PrimaiteGame" = game
        self.agent: ProxyAgent = self.game.rl_agents[0]

    def step(self, action: ActType) -> Tuple[ObsType, SupportsFloat, bool, bool, Dict[str, Any]]:
        """Perform a step in the environment."""
        # make ProxyAgent store the action chosen my the RL policy
        self.agent.store_action(action)
        # apply_agent_actions accesses the action we just stored
        self.game.apply_agent_actions()
        self.game.advance_timestep()
        state = self.game.get_sim_state()

        # Create state suitable for dumping to file.
        dump_state = {self.game.episode_counter: {self.game.step_counter: state}}

        # Dump to file
        # if os.path.isfile(PRIMAITE_PATHS.episode_steps_log_file_path):
        with open(PRIMAITE_PATHS.episode_log_file_path, "a", encoding="utf-8") as f:
            f.write(str(dump_state))
            f.write("\n=================\n")
            f.flush()

        self.game.update_agents(state)

        next_obs = self._get_obs()
        reward = self.agent.reward_function.current_reward
        terminated = False
        truncated = self.game.calculate_truncated()
        info = {}
        print(f"Episode: {self.game.episode_counter}, Step: {self.game.step_counter}, Reward: {reward}")
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


class PrimaiteRayEnv(gymnasium.Env):
    """Ray wrapper that accepts a single `env_config` parameter in init function for compatibility with Ray."""

    def __init__(self, env_config: Dict[str, PrimaiteGame]) -> None:
        """Initialise the environment.

        :param env_config: A dictionary containing the environment configuration. It must contain a single key, `game`
            which is the PrimaiteGame instance.
        :type env_config: Dict[str, PrimaiteGame]
        """
        self.env = PrimaiteGymEnv(game=env_config["game"])
        self.action_space = self.env.action_space
        self.observation_space = self.env.observation_space

    def reset(self, *, seed: int = None, options: dict = None) -> Tuple[ObsType, Dict]:
        """Reset the environment."""
        return self.env.reset(seed=seed)

    def step(self, action: ActType) -> Tuple[ObsType, SupportsFloat, bool, bool, Dict]:
        """Perform a step in the environment."""
        return self.env.step(action)


class PrimaiteRayMARLEnv(MultiAgentEnv):
    """Ray Environment that inherits from MultiAgentEnv to allow training MARL systems."""

    def __init__(self, env_config: Optional[Dict] = None) -> None:
        """Initialise the environment.

        :param env_config: A dictionary containing the environment configuration. It must contain a single key, `game`
            which is the PrimaiteGame instance.
        :type env_config: Dict[str, PrimaiteGame]
        """
        self.game: PrimaiteGame = env_config["game"]
        """Reference to the primaite game"""
        self.agents: Final[Dict[str, ProxyAgent]] = {agent.agent_name: agent for agent in self.game.rl_agents}
        """List of all possible agents in the environment. This list should not change!"""
        self._agent_ids = list(self.agents.keys())

        self.terminateds = set()
        self.truncateds = set()
        self.observation_space = gymnasium.spaces.Dict(
            {name: agent.observation_manager.space for name, agent in self.agents.items()}
        )
        self.action_space = gymnasium.spaces.Dict(
            {name: agent.action_manager.space for name, agent in self.agents.items()}
        )
        super().__init__()

    def reset(self, *, seed: int = None, options: dict = None) -> Tuple[ObsType, Dict]:
        """Reset the environment."""
        self.game.reset()
        state = self.game.get_sim_state()
        self.game.update_agents(state)
        next_obs = self._get_obs()
        info = {}
        return next_obs, info

    def step(
        self, actions: Dict[str, ActType]
    ) -> Tuple[Dict[str, ObsType], Dict[str, SupportsFloat], Dict[str, bool], Dict[str, bool], Dict]:
        """Perform a step in the environment. Adherent to Ray MultiAgentEnv step API.

        :param actions: Dict of actions. The key is agent identifier and the value is a gymnasium action instance.
        :type actions: Dict[str, ActType]
        :return: Observations, rewards, terminateds, truncateds, and info. Each one is a dictionary keyed by agent
            identifier.
        :rtype: Tuple[Dict[str,ObsType], Dict[str, SupportsFloat], Dict[str,bool], Dict[str,bool], Dict]
        """
        # 1. Perform actions
        for agent_name, action in actions.items():
            self.agents[agent_name].store_action(action)
        self.game.apply_agent_actions()

        # 2. Advance timestep
        self.game.advance_timestep()

        # 3. Get next observations
        state = self.game.get_sim_state()
        self.game.update_agents(state)
        next_obs = self._get_obs()

        # 4. Get rewards
        rewards = {name: agent.reward_function.current_reward for name, agent in self.agents.items()}
        terminateds = {name: False for name, _ in self.agents.items()}
        truncateds = {name: self.game.calculate_truncated() for name, _ in self.agents.items()}
        infos = {}
        terminateds["__all__"] = len(self.terminateds) == len(self.agents)
        truncateds["__all__"] = self.game.calculate_truncated()
        return next_obs, rewards, terminateds, truncateds, infos

    def _get_obs(self) -> Dict[str, ObsType]:
        """Return the current observation."""
        return {name: agent.observation_manager.current_observation for name, agent in self.agents.items()}
