from __future__ import annotations
import json
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional, Final, Dict, Union
from uuid import uuid4

import yaml

import primaite
from primaite import getLogger, SESSIONS_DIR
from primaite.config import lay_down_config
from primaite.config import training_config
from primaite.config.training_config import TrainingConfig
from primaite.environment.primaite_env import Primaite

_LOGGER = getLogger(__name__)


def _get_session_path(session_timestamp: datetime) -> Path:
    """
    Get a temp directory session path the test session will output to.

    :param session_timestamp: This is the datetime that the session started.
    :return: The session directory path.
    """
    date_dir = session_timestamp.strftime("%Y-%m-%d")
    session_path = session_timestamp.strftime("%Y-%m-%d_%H-%M-%S")
    session_path = SESSIONS_DIR / date_dir / session_path
    session_path.mkdir(exist_ok=True, parents=True)

    return session_path


class AgentSessionABC(ABC):

    @abstractmethod
    def __init__(
            self,
            training_config_path,
            lay_down_config_path
    ):
        if not isinstance(training_config_path, Path):
            training_config_path = Path(training_config_path)
        self._training_config_path: Final[Union[Path]] = training_config_path
        self._training_config: Final[TrainingConfig] = training_config.load(
            self._training_config_path
        )

        if not isinstance(lay_down_config_path, Path):
            lay_down_config_path = Path(lay_down_config_path)
        self._lay_down_config_path: Final[Union[Path]] = lay_down_config_path
        self._lay_down_config: Dict = lay_down_config.load(
            self._lay_down_config_path
        )
        self.output_verbose_level = self._training_config.output_verbose_level

        self._env: Primaite
        self._agent = None
        self._can_learn: bool = False
        self._can_evaluate: bool = False
        self.is_eval = False

        self._uuid = str(uuid4())
        self.session_timestamp: datetime = datetime.now()
        "The session timestamp"
        self.session_path = _get_session_path(self.session_timestamp)
        "The Session path"
        self.checkpoints_path.mkdir(parents=True, exist_ok=True)

    @property
    def timestamp_str(self) -> str:
        """The session timestamp as a string."""
        return self.session_timestamp.strftime("%Y-%m-%d_%H-%M-%S")

    @property
    def learning_path(self) -> Path:
        """The learning outputs path."""
        return self.session_path / "learning"

    @property
    def evaluation_path(self) -> Path:
        """The evaluation outputs path."""
        return self.session_path / "evaluation"

    @property
    def checkpoints_path(self) -> Path:
        """The Session checkpoints path."""
        return self.learning_path / "checkpoints"

    @property
    def uuid(self):
        """The Agent Session UUID."""
        return self._uuid

    def _write_session_metadata_file(self):
        """
        Write the ``session_metadata.json`` file.

        Creates a ``session_metadata.json`` in the ``session_path`` directory
        and adds the following key/value pairs:

        - uuid: The UUID assigned to the session upon instantiation.
        - start_datetime: The date & time the session started in iso format.
        - end_datetime: NULL.
        - total_episodes: NULL.
        - total_time_steps: NULL.
        - env:
            - training_config:
                - All training config items
            - lay_down_config:
                - All lay down config items

        """
        metadata_dict = {
            "uuid": self.uuid,
            "start_datetime": self.session_timestamp.isoformat(),
            "end_datetime": None,
            "learning": {
                "total_episodes": None,
                "total_time_steps": None
            },
            "evaluation": {
                "total_episodes": None,
                "total_time_steps": None
            },
            "env": {
                "training_config": self._training_config.to_dict(
                    json_serializable=True
                ),
                "lay_down_config": self._lay_down_config,
            },
        }
        filepath = self.session_path / "session_metadata.json"
        _LOGGER.debug(f"Writing Session Metadata file: {filepath}")
        with open(filepath, "w") as file:
            json.dump(metadata_dict, file)
            _LOGGER.debug("Finished writing session metadata file")

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

        if not self.is_eval:
            metadata_dict["learning"]["total_episodes"] = self._env.episode_count  # noqa
            metadata_dict["learning"]["total_time_steps"] = self._env.total_step_count  # noqa
        else:
            metadata_dict["evaluation"]["total_episodes"] = self._env.episode_count  # noqa
            metadata_dict["evaluation"]["total_time_steps"] = self._env.total_step_count  # noqa

        filepath = self.session_path / "session_metadata.json"
        _LOGGER.debug(f"Updating Session Metadata file: {filepath}")
        with open(filepath, "w") as file:
            json.dump(metadata_dict, file)
            _LOGGER.debug("Finished updating session metadata file")

    @abstractmethod
    def _setup(self):
        _LOGGER.info(
            "Welcome to the Primary-level AI Training Environment "
            f"(PrimAITE) (version: {primaite.__version__})"
        )
        _LOGGER.info(
            f"The output directory for this session is: {self.session_path}"
        )
        self._write_session_metadata_file()
        self._can_learn = True
        self._can_evaluate = False

    @abstractmethod
    def _save_checkpoint(self):
        pass

    @abstractmethod
    def learn(
            self,
            time_steps: Optional[int] = None,
            episodes: Optional[int] = None,
            **kwargs
    ):
        if self._can_learn:
            _LOGGER.info("Finished learning")
            _LOGGER.debug("Writing transactions")
            self._update_session_metadata_file()
            self._can_evaluate = True
            self.is_eval = False

    @abstractmethod
    def evaluate(
            self,
            time_steps: Optional[int] = None,
            episodes: Optional[int] = None,
            **kwargs
    ):
        self.is_eval = True
        _LOGGER.info("Finished evaluation")

    @abstractmethod
    def _get_latest_checkpoint(self):
        pass

    @classmethod
    @abstractmethod
    def load(cls, path: Union[str, Path]) -> AgentSessionABC:
        if not isinstance(path, Path):
            path = Path(path)

        if path.exists():
            # Unpack the session_metadata.json file
            md_file = path / "session_metadata.json"
            with open(md_file, "r") as file:
                md_dict = json.load(file)

            # Create a temp directory and dump the training and lay down
            # configs into it
            temp_dir = path / ".temp"
            temp_dir.mkdir(exist_ok=True)

            temp_tc = temp_dir / "tc.yaml"
            with open(temp_tc, "w") as file:
                yaml.dump(md_dict["env"]["training_config"], file)

            temp_ldc = temp_dir / "ldc.yaml"
            with open(temp_ldc, "w") as file:
                yaml.dump(md_dict["env"]["lay_down_config"], file)

            agent = cls(temp_tc, temp_ldc)

            agent.session_path = path

            return agent

        else:
            # Session path does not exist
            msg = f"Failed to load PrimAITE Session, path does not exist: {path}"
            _LOGGER.error(msg)
            raise FileNotFoundError(msg)
        pass

    @abstractmethod
    def save(self):
        self._agent.save(self.session_path)

    @abstractmethod
    def export(self):
        pass


class HardCodedAgentSessionABC(AgentSessionABC):
    def __init__(self, training_config_path, lay_down_config_path):
        super().__init__(training_config_path, lay_down_config_path)
        self._setup()

    def _setup(self):
        self._env: Primaite = Primaite(
            training_config_path=self._training_config_path,
            lay_down_config_path=self._lay_down_config_path,
            session_path=self.session_path,
            timestamp_str=self.timestamp_str
        )
        super()._setup()
        self._can_learn = False
        self._can_evaluate = True


    def _save_checkpoint(self):
        pass

    def _get_latest_checkpoint(self):
        pass

    def learn(
            self,
            time_steps: Optional[int] = None,
            episodes: Optional[int] = None,
            **kwargs
    ):
        _LOGGER.warning("Deterministic agents cannot learn")

    @abstractmethod
    def _calculate_action(self, obs):
        pass

    def evaluate(
            self,
            time_steps: Optional[int] = None,
            episodes: Optional[int] = None,
            **kwargs
    ):
        if not time_steps:
            time_steps = self._training_config.num_steps

        if not episodes:
            episodes = self._training_config.num_episodes

        for episode in range(episodes):
            # Reset env and collect initial observation
            obs = self._env.reset()
            for step in range(time_steps):
                # Calculate action
                action = self._calculate_action(obs)

                # Perform the step
                obs, reward, done, info = self._env.step(action)

                if done:
                    break

                # Introduce a delay between steps
                time.sleep(self._training_config.time_delay / 1000)
        self._env.close()
        super().evaluate()

    @classmethod
    def load(cls):
        _LOGGER.warning("Deterministic agents cannot be loaded")

    def save(self):
        _LOGGER.warning("Deterministic agents cannot be saved")

    def export(self):
        _LOGGER.warning("Deterministic agents cannot be exported")
