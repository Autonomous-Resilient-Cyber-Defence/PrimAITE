import glob
import time
from enum import Enum
from pathlib import Path
from typing import Union, Optional

from ray.rllib.algorithms import Algorithm
from ray.rllib.algorithms.ppo import PPOConfig
from ray.tune.registry import register_env

from primaite.agents.agent import AgentSessionABC
from primaite.config import training_config
from primaite.environment.primaite_env import Primaite


def _env_creator(env_config):
    return Primaite(
        training_config_path=env_config["training_config_path"],
        lay_down_config_path=env_config["lay_down_config_path"],
        transaction_list=env_config["transaction_list"],
        session_path=env_config["session_path"],
        timestamp_str=env_config["timestamp_str"]
    )


class RLlibPPO(AgentSessionABC):

    def __init__(
            self,
            training_config_path,
            lay_down_config_path
    ):
        super().__init__(training_config_path, lay_down_config_path)
        self._ppo_config: PPOConfig
        self._current_result: dict
        self._setup()
        self._agent.save()

    def _setup(self):
        super()._setup()
        register_env("primaite", _env_creator)
        self._ppo_config = PPOConfig()

        self._ppo_config.environment(
            env="primaite",
            env_config=dict(
                training_config_path=self._training_config_path,
                lay_down_config_path=self._lay_down_config_path,
                transaction_list=[],
                session_path=self.session_path,
                timestamp_str=self.timestamp_str
            )
        )

        self._ppo_config.training(
            train_batch_size=self._training_config.num_steps
        )
        self._ppo_config.framework(
            framework=self._training_config.deep_learning_framework.value
        )

        self._ppo_config.rollouts(
            num_rollout_workers=1,
            num_envs_per_worker=1,
            horizon=self._training_config.num_steps
        )
        self._agent: Algorithm = self._ppo_config.build()

    def _save_checkpoint(self):
        checkpoint_n = self._training_config.checkpoint_every_n_episodes
        episode_count = self._current_result["episodes_total"]
        if checkpoint_n > 0 and episode_count > 0:
            if (
                    (episode_count % checkpoint_n == 0)
                    or (episode_count == self._training_config.num_episodes)
            ):
                self._agent.save(self.checkpoints_path)

    def learn(
            self,
            time_steps: Optional[int] = None,
            episodes: Optional[int] = None,
            **kwargs
    ):
        # Temporarily override train_batch_size and horizon
        if time_steps:
            self._ppo_config.train_batch_size = time_steps
            self._ppo_config.horizon = time_steps

        if not episodes:
            episodes = self._training_config.num_episodes

        for i in range(episodes):
            self._current_result = self._agent.train()
            self._save_checkpoint()
        self._agent.stop()
        super().learn()

    def evaluate(
            self,
            time_steps: Optional[int] = None,
            episodes: Optional[int] = None,
            **kwargs
    ):
        raise NotImplementedError

    def _get_latest_checkpoint(self):
        raise NotImplementedError

    @classmethod
    def load(cls):
        raise NotImplementedError

    def save(self):
        raise NotImplementedError

    def export(self):
        raise NotImplementedError
