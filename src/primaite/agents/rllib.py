# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
from __future__ import annotations

import json
import shutil
import zipfile
from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union
from uuid import uuid4

from ray.rllib.algorithms import Algorithm
from ray.rllib.algorithms.a2c import A2CConfig
from ray.rllib.algorithms.ppo import PPOConfig
from ray.tune.logger import UnifiedLogger
from ray.tune.registry import register_env

from primaite import getLogger
from primaite.agents.agent_abc import AgentSessionABC
from primaite.common.enums import AgentFramework, AgentIdentifier, SessionType
from primaite.environment.primaite_env import Primaite
from primaite.exceptions import RLlibAgentError

_LOGGER: Logger = getLogger(__name__)


# TODO: verify type of env_config
def _env_creator(env_config: Dict[str, Any]) -> Primaite:
    return Primaite(
        training_config_path=env_config["training_config_path"],
        lay_down_config_path=env_config["lay_down_config_path"],
        session_path=env_config["session_path"],
        timestamp_str=env_config["timestamp_str"],
    )


# TODO: verify type hint return type
def _custom_log_creator(session_path: Path) -> Callable[[Dict], UnifiedLogger]:
    logdir = session_path / "ray_results"
    logdir.mkdir(parents=True, exist_ok=True)

    def logger_creator(config: Dict) -> UnifiedLogger:
        return UnifiedLogger(config, logdir, loggers=None)

    return logger_creator


class RLlibAgent(AgentSessionABC):
    """An AgentSession class that implements a Ray RLlib agent."""

    def __init__(
        self,
        training_config_path: Optional[Union[str, Path]] = "",
        lay_down_config_path: Optional[Union[str, Path]] = "",
        session_path: Optional[Union[str, Path]] = None,
    ) -> None:
        """
        Initialise the RLLib Agent training session.

        :param training_config_path: YAML file containing configurable items defined in
            `primaite.config.training_config.TrainingConfig`
        :type training_config_path: Union[path, str]
        :param lay_down_config_path: YAML file containing configurable items for generating network laydown.
        :type lay_down_config_path: Union[path, str]
        :raises ValueError: If the training config contains an unexpected value for agent_framework (should be "RLLIB")
        :raises ValueError: If the training config contains an unexpected value for agent_identifies (should be `PPO`
            or `A2C`)
        """
        # TODO: implement RLlib agent loading
        if session_path is not None:
            msg = "RLlib agent loading has not been implemented yet"
            _LOGGER.critical(msg)
            raise NotImplementedError(msg)

        super().__init__(training_config_path, lay_down_config_path)
        if self._training_config.session_type == SessionType.EVAL:
            msg = "Cannot evaluate an RLlib agent that hasn't been through training yet."
            _LOGGER.critical(msg)
            raise RLlibAgentError(msg)
        if not self._training_config.agent_framework == AgentFramework.RLLIB:
            msg = f"Expected RLLIB agent_framework, " f"got {self._training_config.agent_framework}"
            _LOGGER.error(msg)
            raise ValueError(msg)
        self._agent_config_class: Union[PPOConfig, A2CConfig]
        if self._training_config.agent_identifier == AgentIdentifier.PPO:
            self._agent_config_class = PPOConfig
        elif self._training_config.agent_identifier == AgentIdentifier.A2C:
            self._agent_config_class = A2CConfig
        else:
            msg = "Expected PPO or A2C agent_identifier, " f"got {self._training_config.agent_identifier.value}"
            _LOGGER.error(msg)
            raise ValueError(msg)
        self._agent_config: Union[PPOConfig, A2CConfig]

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
        self._train_agent = None  # Required to capture the learning agent to close after eval

    def _update_session_metadata_file(self) -> None:
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
        if not self.is_eval:
            metadata_dict["learning"]["total_episodes"] = self._current_result["episodes_total"]  # noqa
            metadata_dict["learning"]["total_time_steps"] = self._current_result["timesteps_total"]  # noqa
        else:
            metadata_dict["evaluation"]["total_episodes"] = self._current_result["episodes_total"]  # noqa
            metadata_dict["evaluation"]["total_time_steps"] = self._current_result["timesteps_total"]  # noqa

        filepath = self.session_path / "session_metadata.json"
        _LOGGER.debug(f"Updating Session Metadata file: {filepath}")
        with open(filepath, "w") as file:
            json.dump(metadata_dict, file)
            _LOGGER.debug("Finished updating session metadata file")

    def _setup(self) -> None:
        super()._setup()
        register_env("primaite", _env_creator)
        self._agent_config = self._agent_config_class()

        self._agent_config.environment(
            env="primaite",
            env_config=dict(
                training_config_path=self._training_config_path,
                lay_down_config_path=self._lay_down_config_path,
                session_path=self.session_path,
                timestamp_str=self.timestamp_str,
            ),
        )
        self._agent_config.seed = self._training_config.seed

        self._agent_config.training(train_batch_size=self._training_config.num_train_steps)
        self._agent_config.framework(framework="tf")

        self._agent_config.rollouts(
            num_rollout_workers=1,
            num_envs_per_worker=1,
            horizon=self._training_config.num_train_steps,
        )
        self._agent: Algorithm = self._agent_config.build(logger_creator=_custom_log_creator(self.learning_path))

    def _save_checkpoint(self) -> None:
        checkpoint_n = self._training_config.checkpoint_every_n_episodes
        episode_count = self._current_result["episodes_total"]
        save_checkpoint = False
        if checkpoint_n:
            save_checkpoint = episode_count % checkpoint_n == 0
        if episode_count and save_checkpoint:
            self._agent.save(str(self.checkpoints_path))

    def learn(
        self,
        **kwargs: Any,
    ) -> None:
        """
        Evaluate the agent.

        :param kwargs: Any agent-specific key-word args to be passed.
        """
        time_steps = self._training_config.num_train_steps
        episodes = self._training_config.num_train_episodes

        _LOGGER.info(f"Beginning learning for {episodes} episodes @" f" {time_steps} time steps...")
        for i in range(episodes):
            self._current_result = self._agent.train()
            self._save_checkpoint()
        self.save()
        super().learn()
        # Done this way as the RLlib eval can only be performed if the session hasn't been stopped
        if self._training_config.session_type is not SessionType.TRAIN:
            self._train_agent = self._agent
        else:
            self._agent.stop()
            self._plot_av_reward_per_episode(learning_session=True)

    def _unpack_saved_agent_into_eval(self) -> Path:
        """Unpacks the pre-trained and saved RLlib agent so that it can be reloaded by Ray for eval."""
        agent_restore_path = self.evaluation_path / "agent_restore"
        if agent_restore_path.exists():
            shutil.rmtree(agent_restore_path)
        agent_restore_path.mkdir()
        with zipfile.ZipFile(self._saved_agent_path, "r") as zip_file:
            zip_file.extractall(agent_restore_path)
        return agent_restore_path

    def _setup_eval(self):
        self._can_learn = False
        self._can_evaluate = True
        self._agent.restore(str(self._unpack_saved_agent_into_eval()))

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

        self._setup_eval()

        self._env: Primaite = Primaite(
            self._training_config_path, self._lay_down_config_path, self.session_path, self.timestamp_str
        )

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
                action = self._agent.compute_single_action(observation=obs, explore=False)

                obs, rewards, done, info = self._env.step(action)

        self._env.reset()
        self._env.close()
        super().evaluate()
        # Now we're safe to close the learning agent and write the mean rewards per episode for it
        if self._training_config.session_type is not SessionType.TRAIN:
            self._train_agent.stop()
            self._plot_av_reward_per_episode(learning_session=True)
        # Perform a clean-up of the unpacked agent
        if (self.evaluation_path / "agent_restore").exists():
            shutil.rmtree((self.evaluation_path / "agent_restore"))

    def _get_latest_checkpoint(self) -> None:
        raise NotImplementedError

    @classmethod
    def load(cls, path: Union[str, Path]) -> RLlibAgent:
        """Load an agent from file."""
        raise NotImplementedError

    def save(self, overwrite_existing: bool = True) -> None:
        """Save the agent."""
        # Make temp dir to save in isolation
        temp_dir = self.learning_path / str(uuid4())
        temp_dir.mkdir()

        # Save the agent to the temp dir
        self._agent.save(str(temp_dir))

        # Capture the saved Rllib checkpoint inside the temp directory
        for file in temp_dir.iterdir():
            checkpoint_dir = file
            break

        # Zip the folder
        shutil.make_archive(str(self._saved_agent_path).replace(".zip", ""), "zip", checkpoint_dir)  # noqa

        # Drop the temp directory
        shutil.rmtree(temp_dir)

    def export(self) -> None:
        """Export the agent to transportable file format."""
        raise NotImplementedError
