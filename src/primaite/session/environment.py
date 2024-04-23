import copy
import json
from os import PathLike
from typing import Any, Dict, Optional, SupportsFloat, Tuple, Union

import gymnasium
from gymnasium.core import ActType, ObsType
from ray.rllib.env.multi_agent_env import MultiAgentEnv

from primaite import getLogger
from primaite.game.agent.interface import ProxyAgent
from primaite.game.game import PrimaiteGame
from primaite.session.episode_schedule import build_scheduler, EpisodeScheduler
from primaite.session.io import PrimaiteIO
from primaite.simulator import SIM_OUTPUT

_LOGGER = getLogger(__name__)


class PrimaiteGymEnv(gymnasium.Env):
    """
    Thin wrapper env to provide agents with a gymnasium API.

    This is always a single agent environment since gymnasium is a single agent API. Therefore, we can make some
    assumptions about the agent list always having a list of length 1.
    """

    def __init__(self, game_config: Union[Dict, str, PathLike]):
        """Initialise the environment."""
        super().__init__()
        self.episode_scheduler: EpisodeScheduler = build_scheduler(game_config)
        """Object that returns a config corresponding to the current episode."""
        self.io = PrimaiteIO.from_config(self.episode_scheduler(0).get("io_settings", {}))
        """Handles IO for the environment. This produces sys logs, agent logs, etc."""
        self.game: PrimaiteGame = PrimaiteGame.from_config(self.episode_scheduler(0))
        """Current game."""
        self._agent_name = next(iter(self.game.rl_agents))
        """Name of the RL agent. Since there should only be one RL agent we can just pull the first and only key."""

        self.episode_counter: int = 0
        """Current episode number."""

    @property
    def agent(self) -> ProxyAgent:
        """Grab a fresh reference to the agent object because it will be reinstantiated each episode."""
        return self.game.rl_agents[self._agent_name]

    def step(self, action: ActType) -> Tuple[ObsType, SupportsFloat, bool, bool, Dict[str, Any]]:
        """Perform a step in the environment."""
        # make ProxyAgent store the action chosen by the RL policy
        step = self.game.step_counter
        self.agent.store_action(action)
        # apply_agent_actions accesses the action we just stored
        self.game.pre_timestep()
        self.game.apply_agent_actions()
        self.game.advance_timestep()
        state = self.game.get_sim_state()
        self.game.update_agents(state)

        next_obs = self._get_obs()  # this doesn't update observation, just gets the current observation
        reward = self.agent.reward_function.current_reward
        terminated = False
        truncated = self.game.calculate_truncated()
        info = {
            "agent_actions": {name: agent.action_history[-1] for name, agent in self.game.agents.items()}
        }  # tell us what all the agents did for convenience.
        if self.game.save_step_metadata:
            self._write_step_metadata_json(step, action, state, reward)
        return next_obs, reward, terminated, truncated, info

    def _write_step_metadata_json(self, step: int, action: int, state: Dict, reward: int):
        output_dir = SIM_OUTPUT.path / f"episode_{self.episode_counter}" / "step_metadata"

        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"step_{step}.json"

        data = {
            "episode": self.episode_counter,
            "step": step,
            "action": int(action),
            "reward": int(reward),
            "state": state,
        }
        with open(path, "w") as file:
            json.dump(data, file)

    def reset(self, seed: Optional[int] = None) -> Tuple[ObsType, Dict[str, Any]]:
        """Reset the environment."""
        _LOGGER.info(
            f"Resetting environment, episode {self.episode_counter}, "
            f"avg. reward: {self.agent.reward_function.total_reward}"
        )
        if self.io.settings.save_agent_actions:
            all_agent_actions = {name: agent.action_history for name, agent in self.game.agents.items()}
            self.io.write_agent_actions(agent_actions=all_agent_actions, episode=self.episode_counter)
        self.episode_counter += 1
        self.game: PrimaiteGame = PrimaiteGame.from_config(cfg=self.episode_scheduler(self.episode_counter))
        self.game.setup_for_episode(episode=self.episode_counter)
        state = self.game.get_sim_state()
        self.game.update_agents(state=state)
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
        if self.agent.flatten_obs:
            return gymnasium.spaces.flatten_space(self.agent.observation_manager.space)
        else:
            return self.agent.observation_manager.space

    def _get_obs(self) -> ObsType:
        """Return the current observation."""
        if self.agent.flatten_obs:
            unflat_space = self.agent.observation_manager.space
            unflat_obs = self.agent.observation_manager.current_observation
            return gymnasium.spaces.flatten(unflat_space, unflat_obs)
        else:
            return self.agent.observation_manager.current_observation

    def close(self):
        """Close the simulation."""
        if self.io.settings.save_agent_actions:
            all_agent_actions = {name: agent.action_history for name, agent in self.game.agents.items()}
            self.io.write_agent_actions(agent_actions=all_agent_actions, episode=self.episode_counter)


class PrimaiteRayEnv(gymnasium.Env):
    """Ray wrapper that accepts a single `env_config` parameter in init function for compatibility with Ray."""

    def __init__(self, env_config: Dict) -> None:
        """Initialise the environment.

        :param env_config: A dictionary containing the environment configuration.
        :type env_config: Dict
        """
        self.env = PrimaiteGymEnv(game_config=env_config)
        self.env.episode_counter -= 1
        self.action_space = self.env.action_space
        self.observation_space = self.env.observation_space

    def reset(self, *, seed: int = None, options: dict = None) -> Tuple[ObsType, Dict]:
        """Reset the environment."""
        return self.env.reset(seed=seed)

    def step(self, action: ActType) -> Tuple[ObsType, SupportsFloat, bool, bool, Dict]:
        """Perform a step in the environment."""
        return self.env.step(action)

    def close(self):
        """Close the simulation."""
        self.env.close()


class PrimaiteRayMARLEnv(MultiAgentEnv):
    """Ray Environment that inherits from MultiAgentEnv to allow training MARL systems."""

    def __init__(self, env_config: Dict) -> None:
        """Initialise the environment.

        :param env_config: A dictionary containing the environment configuration. It must contain a single key, `game`
            which is the PrimaiteGame instance.
        :type env_config: Dict
        """
        self.game_config: Dict = env_config
        """PrimaiteGame definition. This can be changed between episodes to enable curriculum learning."""
        self.io = PrimaiteIO.from_config(env_config.get("io_settings"))
        """Handles IO for the environment. This produces sys logs, agent logs, etc."""
        self.game: PrimaiteGame = PrimaiteGame.from_config(copy.deepcopy(self.game_config))
        """Reference to the primaite game"""
        self._agent_ids = list(self.game.rl_agents.keys())
        """Agent ids. This is a list of strings of agent names."""
        self.episode_counter: int = 0
        """Current episode number."""

        self.terminateds = set()
        self.truncateds = set()
        self.observation_space = gymnasium.spaces.Dict(
            {
                name: gymnasium.spaces.flatten_space(agent.observation_manager.space)
                for name, agent in self.agents.items()
            }
        )
        self.action_space = gymnasium.spaces.Dict(
            {name: agent.action_manager.space for name, agent in self.agents.items()}
        )

        super().__init__()

    @property
    def agents(self) -> Dict[str, ProxyAgent]:
        """Grab a fresh reference to the agents from this episode's game object."""
        return {name: self.game.rl_agents[name] for name in self._agent_ids}

    def reset(self, *, seed: int = None, options: dict = None) -> Tuple[ObsType, Dict]:
        """Reset the environment."""
        if self.io.settings.save_agent_actions:
            all_agent_actions = {name: agent.action_history for name, agent in self.game.agents.items()}
            self.io.write_agent_actions(agent_actions=all_agent_actions, episode=self.episode_counter)
        self.game: PrimaiteGame = PrimaiteGame.from_config(cfg=copy.deepcopy(self.game_config))
        self.game.setup_for_episode(episode=self.episode_counter)
        self.episode_counter += 1
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
        step = self.game.step_counter
        # 1. Perform actions
        for agent_name, action in actions.items():
            self.agents[agent_name].store_action(action)
        self.game.pre_timestep()
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
        infos = {name: {} for name, _ in self.agents.items()}
        terminateds["__all__"] = len(self.terminateds) == len(self.agents)
        truncateds["__all__"] = self.game.calculate_truncated()
        if self.game.save_step_metadata:
            self._write_step_metadata_json(step, actions, state, rewards)
        return next_obs, rewards, terminateds, truncateds, infos

    def _write_step_metadata_json(self, step: int, actions: Dict, state: Dict, rewards: Dict):
        output_dir = SIM_OUTPUT.path / f"episode_{self.episode_counter}" / "step_metadata"

        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"step_{step}.json"

        data = {
            "episode": self.episode_counter,
            "step": step,
            "actions": {agent_name: int(action) for agent_name, action in actions.items()},
            "reward": rewards,
            "state": state,
        }
        with open(path, "w") as file:
            json.dump(data, file)

    def _get_obs(self) -> Dict[str, ObsType]:
        """Return the current observation."""
        obs = {}
        for agent_name in self._agent_ids:
            agent = self.game.rl_agents[agent_name]
            unflat_space = agent.observation_manager.space
            unflat_obs = agent.observation_manager.current_observation
            obs[agent_name] = gymnasium.spaces.flatten(unflat_space, unflat_obs)
        return obs

    def close(self):
        """Close the simulation."""
        if self.io.settings.save_agent_actions:
            all_agent_actions = {name: agent.action_history for name, agent in self.game.agents.items()}
            self.io.write_agent_actions(agent_actions=all_agent_actions, episode=self.episode_counter)
