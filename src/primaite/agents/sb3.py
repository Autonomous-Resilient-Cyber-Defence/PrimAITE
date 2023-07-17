from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Union

import numpy as np
from stable_baselines3 import A2C, PPO
from stable_baselines3.ppo import MlpPolicy as PPOMlp

from primaite import getLogger
from primaite.agents.agent_abc import AgentSessionABC
from primaite.common.enums import AgentFramework, AgentIdentifier
from primaite.environment.primaite_env import Primaite

_LOGGER = getLogger(__name__)


class SB3Agent(AgentSessionABC):
    """An AgentSession class that implements a Stable Baselines3 agent."""

    def __init__(
        self,
        training_config_path: Optional[Union[str, Path]] = None,
        lay_down_config_path: Optional[Union[str, Path]] = None,
        session_path: Optional[Union[str, Path]] = None,
    ):
        """
        Initialise the SB3 Agent training session.

        :param training_config_path: YAML file containing configurable items defined in
            `primaite.config.training_config.TrainingConfig`
        :type training_config_path: Union[path, str]
        :param lay_down_config_path: YAML file containing configurable items for generating network laydown.
        :type lay_down_config_path: Union[path, str]
        :raises ValueError: If the training config contains an unexpected value for agent_framework (should be "SB3")
        :raises ValueError: If the training config contains an unexpected value for agent_identifies (should be `PPO`
            or `A2C`)
        """
        super().__init__(training_config_path, lay_down_config_path, session_path)
        if not self._training_config.agent_framework == AgentFramework.SB3:
            msg = f"Expected SB3 agent_framework, " f"got {self._training_config.agent_framework}"
            _LOGGER.error(msg)
            raise ValueError(msg)
        if self._training_config.agent_identifier == AgentIdentifier.PPO:
            self._agent_class = PPO
        elif self._training_config.agent_identifier == AgentIdentifier.A2C:
            self._agent_class = A2C
        else:
            msg = "Expected PPO or A2C agent_identifier, " f"got {self._training_config.agent_identifier}"
            _LOGGER.error(msg)
            raise ValueError(msg)

        self._tensorboard_log_path = self.learning_path / "tensorboard_logs"
        self._tensorboard_log_path.mkdir(parents=True, exist_ok=True)

        _LOGGER.debug(
            f"Created {self.__class__.__name__} using: "
            f"agent_framework={self._training_config.agent_framework}, "
            f"agent_identifier="
            f"{self._training_config.agent_identifier}"
        )

        self.is_eval = False

        self._setup()

    def _setup(self):
        """Set up the SB3 Agent."""
        self._env = Primaite(
            training_config_path=self._training_config_path,
            lay_down_config_path=self._lay_down_config_path,
            session_path=self.session_path,
            timestamp_str=self.timestamp_str,
        )

        # check if there is a zip file that needs to be loaded
        load_file = next(self.session_path.rglob("*.zip"), None)

        if not load_file:
            # create a new env and agent

            self._agent = self._agent_class(
                PPOMlp,
                self._env,
                verbose=self.sb3_output_verbose_level,
                n_steps=self._training_config.num_train_steps,
                tensorboard_log=str(self._tensorboard_log_path),
                seed=self._training_config.seed,
            )
        else:
            # set env values from session metadata
            with open(self.session_path / "session_metadata.json", "r") as file:
                md_dict = json.load(file)

            # load environment values
            if self.is_eval:
                # evaluation always starts at 0
                self._env.episode_count = 0
                self._env.total_step_count = 0
            else:
                # carry on from previous learning sessions
                self._env.episode_count = md_dict["learning"]["total_episodes"]
                self._env.total_step_count = md_dict["learning"]["total_time_steps"]

            # load the file
            self._agent = self._agent_class.load(load_file, env=self._env)

            # set agent values
            self._agent.verbose = self.sb3_output_verbose_level
            self._agent.tensorboard_log = self.session_path / "learning/tensorboard_logs"

        super()._setup()

    def _save_checkpoint(self):
        checkpoint_n = self._training_config.checkpoint_every_n_episodes
        episode_count = self._env.episode_count
        save_checkpoint = False
        if checkpoint_n:
            save_checkpoint = episode_count % checkpoint_n == 0
        if episode_count and save_checkpoint:
            checkpoint_path = self.checkpoints_path / f"sb3ppo_{episode_count}.zip"
            self._agent.save(checkpoint_path)
            _LOGGER.debug(f"Saved agent checkpoint: {checkpoint_path}")

    def _get_latest_checkpoint(self):
        pass

    def learn(
        self,
        **kwargs,
    ):
        """
        Train the agent.

        :param kwargs: Any agent-specific key-word args to be passed.
        """
        time_steps = self._training_config.num_train_steps
        episodes = self._training_config.num_train_episodes
        self.is_eval = False
        _LOGGER.info(f"Beginning learning for {episodes} episodes @" f" {time_steps} time steps...")
        for i in range(episodes):
            self._agent.learn(total_timesteps=time_steps)
            self._save_checkpoint()
        self._env._write_av_reward_per_episode()  # noqa
        self.save()
        self._env.close()
        super().learn()

        # save agent
        self.save()

    def evaluate(
        self,
        **kwargs,
    ):
        """
        Evaluate the agent.

        :param kwargs: Any agent-specific key-word args to be passed.
        """
        time_steps = self._training_config.num_eval_steps
        episodes = self._training_config.num_eval_episodes
        self._env.set_as_eval()
        self.is_eval = True
        if self._training_config.deterministic:
            deterministic_str = "deterministic"
        else:
            deterministic_str = "non-deterministic"
        _LOGGER.info(
            f"Beginning {deterministic_str} evaluation for " f"{episodes} episodes @ {time_steps} time steps..."
        )
        for episode in range(episodes):
            obs = self._env.reset()

            for step in range(time_steps):
                action, _states = self._agent.predict(obs, deterministic=self._training_config.deterministic)
                if isinstance(action, np.ndarray):
                    action = np.int64(action)
                obs, rewards, done, info = self._env.step(action)
        self._env._write_av_reward_per_episode()  # noqa
        self._env.close()
        super().evaluate()

    def save(self):
        """Save the agent."""
        self._agent.save(self._saved_agent_path)

    def export(self):
        """Export the agent to transportable file format."""
        raise NotImplementedError
