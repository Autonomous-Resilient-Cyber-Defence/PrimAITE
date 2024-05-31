import json
from os import PathLike
from typing import Any, Dict, Optional, SupportsFloat, Tuple, Union

import gymnasium
from gymnasium.core import ActType, ObsType

from primaite import getLogger
from primaite.game.agent.interface import ProxyAgent
from primaite.game.game import PrimaiteGame
from primaite.session.episode_schedule import build_scheduler, EpisodeScheduler
from primaite.session.io import PrimaiteIO
from primaite.simulator import SIM_OUTPUT
from primaite.simulator.system.core.packet_capture import PacketCapture

_LOGGER = getLogger(__name__)


class PrimaiteGymEnv(gymnasium.Env):
    """
    Thin wrapper env to provide agents with a gymnasium API.

    This is always a single agent environment since gymnasium is a single agent API. Therefore, we can make some
    assumptions about the agent list always having a list of length 1.
    """

    def __init__(self, env_config: Union[Dict, str, PathLike]):
        """Initialise the environment."""
        super().__init__()
        self.episode_scheduler: EpisodeScheduler = build_scheduler(env_config)
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
        self.game.pre_timestep()
        # apply_agent_actions accesses the action we just stored
        self.game.apply_agent_actions()
        self.game.advance_timestep()
        state = self.game.get_sim_state()
        self.game.update_agents(state)

        next_obs = self._get_obs()  # this doesn't update observation, just gets the current observation
        reward = self.agent.reward_function.current_reward
        _LOGGER.info(f"step: {self.game.step_counter}, Blue reward: {reward}")
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

    def reset(self, seed: Optional[int] = None, options: Optional[Dict] = None) -> Tuple[ObsType, Dict[str, Any]]:
        """Reset the environment."""
        _LOGGER.info(
            f"Resetting environment, episode {self.episode_counter}, "
            f"avg. reward: {self.agent.reward_function.total_reward}"
        )
        if self.io.settings.save_agent_actions:
            all_agent_actions = {name: agent.action_history for name, agent in self.game.agents.items()}
            self.io.write_agent_actions(agent_actions=all_agent_actions, episode=self.episode_counter)
        self.episode_counter += 1
        PacketCapture.clear()
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
