from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, Final, Union
from uuid import uuid4

import yaml

import primaite
from primaite import getLogger, SESSIONS_DIR
from primaite.config import lay_down_config, training_config
from primaite.config.training_config import TrainingConfig
from primaite.data_viz.session_plots import plot_av_reward_per_episode
from primaite.environment.primaite_env import Primaite

_LOGGER = getLogger(__name__)


def get_session_path(session_timestamp: datetime) -> Path:
    """Get the directory path the session will output to.

    This is set in the format of:
        ~/primaite/sessions/<yyyy-mm-dd>/<yyyy-mm-dd>_<hh-mm-ss>.

    :param session_timestamp: This is the datetime that the session started.
    :return: The session directory path.
    """
    date_dir = session_timestamp.strftime("%Y-%m-%d")
    session_path = session_timestamp.strftime("%Y-%m-%d_%H-%M-%S")
    session_path = SESSIONS_DIR / date_dir / session_path
    session_path.mkdir(exist_ok=True, parents=True)

    return session_path


class AgentSessionABC(ABC):
    """
    An ABC that manages training and/or evaluation of agents in PrimAITE.

    This class cannot be directly instantiated and must be inherited from with all implemented abstract methods
    implemented.
    """

    @abstractmethod
    def __init__(self, training_config_path, lay_down_config_path):
        """
        Initialise an agent session from config files.

        :param training_config_path: YAML file containing configurable items defined in
            `primaite.config.training_config.TrainingConfig`
        :type training_config_path: Union[path, str]
        :param lay_down_config_path: YAML file containing configurable items for generating network laydown.
        :type lay_down_config_path: Union[path, str]
        """
        if not isinstance(training_config_path, Path):
            training_config_path = Path(training_config_path)
        self._training_config_path: Final[Union[Path, str]] = training_config_path
        self._training_config: Final[TrainingConfig] = training_config.load(self._training_config_path)

        if not isinstance(lay_down_config_path, Path):
            lay_down_config_path = Path(lay_down_config_path)
        self._lay_down_config_path: Final[Union[Path, str]] = lay_down_config_path
        self._lay_down_config: Dict = lay_down_config.load(self._lay_down_config_path)
        self.sb3_output_verbose_level = self._training_config.sb3_output_verbose_level

        self._env: Primaite
        self._agent = None
        self._can_learn: bool = False
        self._can_evaluate: bool = False
        self.is_eval = False

        self._uuid = str(uuid4())
        self.session_timestamp: datetime = datetime.now()
        "The session timestamp"
        self.session_path = get_session_path(self.session_timestamp)
        "The Session path"

    @property
    def timestamp_str(self) -> str:
        """The session timestamp as a string."""
        return self.session_timestamp.strftime("%Y-%m-%d_%H-%M-%S")

    @property
    def learning_path(self) -> Path:
        """The learning outputs path."""
        path = self.session_path / "learning"
        path.mkdir(exist_ok=True, parents=True)
        return path

    @property
    def evaluation_path(self) -> Path:
        """The evaluation outputs path."""
        path = self.session_path / "evaluation"
        path.mkdir(exist_ok=True, parents=True)
        return path

    @property
    def checkpoints_path(self) -> Path:
        """The Session checkpoints path."""
        path = self.learning_path / "checkpoints"
        path.mkdir(exist_ok=True, parents=True)
        return path

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
            "learning": {"total_episodes": None, "total_time_steps": None},
            "evaluation": {"total_episodes": None, "total_time_steps": None},
            "env": {
                "training_config": self._training_config.to_dict(json_serializable=True),
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
            "Welcome to the Primary-level AI Training Environment " f"(PrimAITE) (version: {primaite.__version__})"
        )
        _LOGGER.info(f"The output directory for this session is: {self.session_path}")
        self._write_session_metadata_file()
        self._can_learn = True
        self._can_evaluate = False

    @abstractmethod
    def _save_checkpoint(self):
        pass

    @abstractmethod
    def learn(
        self,
        **kwargs,
    ):
        """Train the agent.

        :param kwargs: Any agent-specific key-word args to be passed.
        """
        if self._can_learn:
            _LOGGER.info("Finished learning")
            _LOGGER.debug("Writing transactions")
            self._update_session_metadata_file()
            self._can_evaluate = True
            self.is_eval = False
            self._plot_av_reward_per_episode(learning_session=True)

    @abstractmethod
    def evaluate(
        self,
        **kwargs,
    ):
        """Evaluate the agent.

        :param kwargs: Any agent-specific key-word args to be passed.
        """
        self._env.set_as_eval()  # noqa
        self.is_eval = True
        self._plot_av_reward_per_episode(learning_session=False)
        _LOGGER.info("Finished evaluation")

    @abstractmethod
    def _get_latest_checkpoint(self):
        pass

    @classmethod
    @abstractmethod
    def load(cls, path: Union[str, Path]) -> AgentSessionABC:
        """Load an agent from file."""
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
        """Save the agent."""
        self._agent.save(self.session_path)

    @abstractmethod
    def export(self):
        """Export the agent to transportable file format."""
        pass

    def close(self):
        """Closes the agent."""
        self._env.episode_av_reward_writer.close()  # noqa
        self._env.transaction_writer.close()  # noqa

    def _plot_av_reward_per_episode(self, learning_session: bool = True):
        # self.close()
        title = f"PrimAITE Session {self.timestamp_str} "
        subtitle = str(self._training_config)
        csv_file = f"average_reward_per_episode_{self.timestamp_str}.csv"
        image_file = f"average_reward_per_episode_{self.timestamp_str}.png"
        if learning_session:
            title += "(Learning)"
            path = self.learning_path / csv_file
            image_path = self.learning_path / image_file
        else:
            title += "(Evaluation)"
            path = self.evaluation_path / csv_file
            image_path = self.evaluation_path / image_file

        fig = plot_av_reward_per_episode(path, title, subtitle)
        fig.write_image(image_path)
        _LOGGER.debug(f"Saved average rewards per episode plot to: {path}")


class HardCodedAgentSessionABC(AgentSessionABC):
    """
    An Agent Session ABC for evaluation deterministic agents.

    This class cannot be directly instantiated and must be inherited from with all implemented abstract methods
    implemented.
    """

    def __init__(self, training_config_path, lay_down_config_path):
        """
        Initialise a hardcoded agent session.

        :param training_config_path: YAML file containing configurable items defined in
            `primaite.config.training_config.TrainingConfig`
        :type training_config_path: Union[path, str]
        :param lay_down_config_path: YAML file containing configurable items for generating network laydown.
        :type lay_down_config_path: Union[path, str]
        """
        super().__init__(training_config_path, lay_down_config_path)
        self._setup()

    def _setup(self):
        self._env: Primaite = Primaite(
            training_config_path=self._training_config_path,
            lay_down_config_path=self._lay_down_config_path,
            session_path=self.session_path,
            timestamp_str=self.timestamp_str,
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
        **kwargs,
    ):
        """Train the agent.

        :param kwargs: Any agent-specific key-word args to be passed.
        """
        _LOGGER.warning("Deterministic agents cannot learn")

    @abstractmethod
    def _calculate_action(self, obs):
        pass

    def evaluate(
        self,
        **kwargs,
    ):
        """Evaluate the agent.

        :param kwargs: Any agent-specific key-word args to be passed.
        """
        self._env.set_as_eval()  # noqa
        self.is_eval = True

        time_steps = self._training_config.num_steps
        episodes = self._training_config.num_episodes

        obs = self._env.reset()
        for episode in range(episodes):
            # Reset env and collect initial observation
            for step in range(time_steps):
                # Calculate action
                action = self._calculate_action(obs)

                # Perform the step
                obs, reward, done, info = self._env.step(action)

                if done:
                    break

                # Introduce a delay between steps
                time.sleep(self._training_config.time_delay / 1000)
            obs = self._env.reset()
        self._env.close()

    @classmethod
    def load(cls):
        """Load an agent from file."""
        _LOGGER.warning("Deterministic agents cannot be loaded")

    def save(self):
        """Save the agent."""
        _LOGGER.warning("Deterministic agents cannot be saved")

    def export(self):
        """Export the agent to transportable file format."""
        _LOGGER.warning("Deterministic agents cannot be exported")
