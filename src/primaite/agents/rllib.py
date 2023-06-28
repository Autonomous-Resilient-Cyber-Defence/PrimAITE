import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from ray.rllib.algorithms import Algorithm
from ray.rllib.algorithms.a2c import A2CConfig
from ray.rllib.algorithms.ppo import PPOConfig
from ray.tune.logger import UnifiedLogger
from ray.tune.registry import register_env
import tensorflow as tf
from primaite import getLogger
from primaite.agents.agent import AgentSessionABC
from primaite.common.enums import AgentFramework, AgentIdentifier, \
    DeepLearningFramework
from primaite.environment.primaite_env import Primaite

_LOGGER = getLogger(__name__)

def _env_creator(env_config):
    return Primaite(
        training_config_path=env_config["training_config_path"],
        lay_down_config_path=env_config["lay_down_config_path"],
        session_path=env_config["session_path"],
        timestamp_str=env_config["timestamp_str"]
    )


def _custom_log_creator(session_path: Path):
    logdir = session_path / "ray_results"
    logdir.mkdir(parents=True, exist_ok=True)

    def logger_creator(config):
        return UnifiedLogger(config, logdir, loggers=None)

    return logger_creator


class RLlibAgent(AgentSessionABC):

    def __init__(
            self,
            training_config_path,
            lay_down_config_path
    ):
        super().__init__(training_config_path, lay_down_config_path)
        if not self._training_config.agent_framework == AgentFramework.RLLIB:
            msg = (f"Expected RLLIB agent_framework, "
                   f"got {self._training_config.agent_framework}")
            _LOGGER.error(msg)
            raise ValueError(msg)
        if self._training_config.agent_identifier == AgentIdentifier.PPO:
            self._agent_config_class = PPOConfig
        elif self._training_config.agent_identifier == AgentIdentifier.A2C:
            self._agent_config_class = A2CConfig
        else:
            msg = ("Expected PPO or A2C agent_identifier, "
                   f"got {self._training_config.agent_identifier.value}")
            _LOGGER.error(msg)
            raise ValueError(msg)
        self._agent_config: PPOConfig

        self._current_result: dict
        self._setup()
        _LOGGER.debug(
            f"Created {self.__class__.__name__} using: "
            f"agent_framework={self._training_config.agent_framework}, "
            f"agent_identifier="
            f"{self._training_config.agent_identifier}, "
            f"deep_learning_framework="
            f"{self._training_config.deep_learning_framework}"
        )

    def _update_session_metadata_file(self):
        """
        Update the ``session_metadata.json`` file.

        Updates the `session_metadata.json`` in the ``session_path`` directory
        with the following key/value pairs:

        - end_datetime: The date & time the session ended in iso format.
        - total_episodes: The total number of training episodes completed.
        - total_time_steps: The total number of training time steps completed.
        """
        with open(self.session_path / "session_metadata.json", "r") as file:
            metadata_dict = json.load(file)

        metadata_dict["end_datetime"] = datetime.now().isoformat()
        metadata_dict["total_episodes"] = self._current_result["episodes_total"]
        metadata_dict["total_time_steps"] = self._current_result["timesteps_total"]

        filepath = self.session_path / "session_metadata.json"
        _LOGGER.debug(f"Updating Session Metadata file: {filepath}")
        with open(filepath, "w") as file:
            json.dump(metadata_dict, file)
            _LOGGER.debug("Finished updating session metadata file")

    def _setup(self):
        super()._setup()
        register_env("primaite", _env_creator)
        self._agent_config = self._agent_config_class()

        self._agent_config.environment(
            env="primaite",
            env_config=dict(
                training_config_path=self._training_config_path,
                lay_down_config_path=self._lay_down_config_path,
                session_path=self.session_path,
                timestamp_str=self.timestamp_str
            )
        )

        self._agent_config.training(
            train_batch_size=self._training_config.num_steps
        )
        self._agent_config.framework(
            framework="tf"
        )

        self._agent_config.rollouts(
            num_rollout_workers=1,
            num_envs_per_worker=1,
            horizon=self._training_config.num_steps
        )
        self._agent: Algorithm = self._agent_config.build(
            logger_creator=_custom_log_creator(self.session_path)
        )


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
            self._agent_config.train_batch_size = time_steps
            self._agent_config.horizon = time_steps

        if not episodes:
            episodes = self._training_config.num_episodes
        _LOGGER.info(f"Beginning learning for {episodes} episodes @"
                     f" {time_steps} time steps...")
        for i in range(episodes):
            self._current_result = self._agent.train()
            self._save_checkpoint()
        if self._training_config.deep_learning_framework != DeepLearningFramework.TORCH:
            policy = self._agent.get_policy()
            tf.compat.v1.summary.FileWriter(
                self.session_path / "ray_results",
                policy.get_session().graph
            )
        super().learn()
        self._agent.stop()

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
