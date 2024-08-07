# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
import json
from typing import Dict, SupportsFloat, Tuple

import gymnasium
from gymnasium import spaces
from gymnasium.core import ActType, ObsType
from ray.rllib.env.multi_agent_env import MultiAgentEnv

from primaite.game.agent.interface import ProxyAgent
from primaite.game.game import PrimaiteGame
from primaite.session.environment import _LOGGER, PrimaiteGymEnv
from primaite.session.episode_schedule import build_scheduler, EpisodeScheduler
from primaite.session.io import PrimaiteIO
from primaite.simulator import SIM_OUTPUT
from primaite.simulator.system.core.packet_capture import PacketCapture


class PrimaiteRayMARLEnv(MultiAgentEnv):
    """Ray Environment that inherits from MultiAgentEnv to allow training MARL systems."""

    def __init__(self, env_config: Dict) -> None:
        """Initialise the environment.

        :param env_config: A dictionary containing the environment configuration. It must contain a single key, `game`
            which is the PrimaiteGame instance.
        :type env_config: Dict
        """
        self.episode_counter: int = 0
        """Current episode number."""
        self.episode_scheduler: EpisodeScheduler = build_scheduler(env_config)
        """Object that returns a config corresponding to the current episode."""
        self.io = PrimaiteIO.from_config(self.episode_scheduler(0).get("io_settings", {}))
        """Handles IO for the environment. This produces sys logs, agent logs, etc."""
        self.game: PrimaiteGame = PrimaiteGame.from_config(self.episode_scheduler(self.episode_counter))
        """Reference to the primaite game"""
        self._agent_ids = list(self.game.rl_agents.keys())
        """Agent ids. This is a list of strings of agent names."""

        self.terminateds = set()
        self.truncateds = set()
        self.observation_space = spaces.Dict(
            {name: spaces.flatten_space(agent.observation_manager.space) for name, agent in self.agents.items()}
        )
        for agent_name in self._agent_ids:
            agent = self.game.rl_agents[agent_name]
            if agent.action_masking:
                self.observation_space[agent_name] = spaces.Dict(
                    {
                        "action_mask": spaces.MultiBinary(agent.action_manager.space.n),
                        "observations": self.observation_space[agent_name],
                    }
                )
        self.action_space = spaces.Dict({name: agent.action_manager.space for name, agent in self.agents.items()})
        self._obs_space_in_preferred_format = True
        self._action_space_in_preferred_format = True
        super().__init__()

    @property
    def agents(self) -> Dict[str, ProxyAgent]:
        """Grab a fresh reference to the agents from this episode's game object."""
        return {name: self.game.rl_agents[name] for name in self._agent_ids}

    def reset(self, *, seed: int = None, options: dict = None) -> Tuple[ObsType, Dict]:
        """Reset the environment."""
        super().reset()  # Ensure PRNG seed is set everywhere
        rewards = {name: agent.reward_function.total_reward for name, agent in self.agents.items()}
        _LOGGER.info(f"Resetting environment, episode {self.episode_counter}, " f"avg. reward: {rewards}")

        if self.io.settings.save_agent_actions:
            all_agent_actions = {name: agent.history for name, agent in self.game.agents.items()}
            self.io.write_agent_log(agent_actions=all_agent_actions, episode=self.episode_counter)

        self.episode_counter += 1
        PacketCapture.clear()
        self.game: PrimaiteGame = PrimaiteGame.from_config(self.episode_scheduler(self.episode_counter))
        self.game.setup_for_episode(episode=self.episode_counter)
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
        _LOGGER.info(f"step: {self.game.step_counter}, Rewards: {rewards}")
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
        all_obs = {}
        for agent_name in self._agent_ids:
            agent = self.game.rl_agents[agent_name]
            unflat_space = agent.observation_manager.space
            unflat_obs = agent.observation_manager.current_observation
            obs = gymnasium.spaces.flatten(unflat_space, unflat_obs)
            if agent.action_masking:
                all_obs[agent_name] = {"action_mask": self.game.action_mask(agent_name), "observations": obs}
            else:
                all_obs[agent_name] = obs
        return all_obs

    def close(self):
        """Close the simulation."""
        if self.io.settings.save_agent_actions:
            all_agent_actions = {name: agent.history for name, agent in self.game.agents.items()}
            self.io.write_agent_log(agent_actions=all_agent_actions, episode=self.episode_counter)


class PrimaiteRayEnv(gymnasium.Env):
    """Ray wrapper that accepts a single `env_config` parameter in init function for compatibility with Ray."""

    def __init__(self, env_config: Dict) -> None:
        """Initialise the environment.

        :param env_config: A dictionary containing the environment configuration.
        :type env_config: Dict
        """
        self.env = PrimaiteGymEnv(env_config=env_config)
        # self.env.episode_counter -= 1
        self.action_space = self.env.action_space
        if self.env.agent.action_masking:
            self.observation_space = spaces.Dict(
                {"action_mask": spaces.MultiBinary(self.env.action_space.n), "observations": self.env.observation_space}
            )
        else:
            self.observation_space = self.env.observation_space

    def reset(self, *, seed: int = None, options: dict = None) -> Tuple[ObsType, Dict]:
        """Reset the environment."""
        super().reset()  # Ensure PRNG seed is set everywhere
        if self.env.agent.action_masking:
            obs, *_ = self.env.reset(seed=seed)
            new_obs = {"action_mask": self.env.action_masks(), "observations": obs}
            return new_obs, *_
        return self.env.reset(seed=seed)

    def step(self, action: ActType) -> Tuple[ObsType, SupportsFloat, bool, bool, Dict]:
        """Perform a step in the environment."""
        # if action masking is enabled, intercept the step method and add action mask to observation
        if self.env.agent.action_masking:
            obs, *_ = self.env.step(action)
            new_obs = {"action_mask": self.game.action_mask(self.env._agent_name), "observations": obs}
            return new_obs, *_
        else:
            return self.env.step(action)

    def close(self):
        """Close the simulation."""
        self.env.close()

    @property
    def game(self) -> PrimaiteGame:
        """Pass through game from env."""
        return self.env.game
