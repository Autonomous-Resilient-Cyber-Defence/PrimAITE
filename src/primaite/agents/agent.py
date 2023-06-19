import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional, Final, Dict, Union, List
from uuid import uuid4

from primaite import getLogger
from primaite.common.enums import OutputVerboseLevel
from primaite.config import lay_down_config
from primaite.config import training_config
from primaite.config.training_config import TrainingConfig
from primaite.environment.primaite_env import Primaite
from primaite.transactions.transactions_to_file import \
    write_transaction_to_file

_LOGGER = getLogger(__name__)


def _get_temp_session_path(session_timestamp: datetime) -> Path:
    """
    Get a temp directory session path the test session will output to.

    :param session_timestamp: This is the datetime that the session started.
    :return: The session directory path.
    """
    date_dir = session_timestamp.strftime("%Y-%m-%d")
    session_path = session_timestamp.strftime("%Y-%m-%d_%H-%M-%S")
    session_path = Path("./") / date_dir / session_path
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
        self._transaction_list: List[Dict] = []
        self._can_learn: bool = False
        self._can_evaluate: bool = False

        self._uuid = str(uuid4())
        self.session_timestamp: datetime = datetime.now()
        "The session timestamp"
        self.session_path = _get_temp_session_path(self.session_timestamp)
        "The Session path"
        self.checkpoints_path = self.session_path / "checkpoints"
        "The Session checkpoints path"

        self.timestamp_str = self.session_timestamp.strftime(
            "%Y-%m-%d_%H-%M-%S")
        "The session timestamp as a string"

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
            "total_episodes": None,
            "total_time_steps": None,
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
        metadata_dict["total_episodes"] = self._env.episode_count
        metadata_dict["total_time_steps"] = self._env.total_step_count

        filepath = self.session_path / "session_metadata.json"
        _LOGGER.debug(f"Updating Session Metadata file: {filepath}")
        with open(filepath, "w") as file:
            json.dump(metadata_dict, file)
            _LOGGER.debug("Finished updating session metadata file")

    @abstractmethod
    def _setup(self):
        if self.output_verbose_level >= OutputVerboseLevel.INFO:
            _LOGGER.info(
                "Welcome to the Primary-level AI Training Environment "
                "(PrimAITE)"
            )
            _LOGGER.debug(
                f"The output directory for this agent is: {self.session_path}"
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
            _LOGGER.debug("Writing transactions")
            write_transaction_to_file(
                transaction_list=self._transaction_list,
                session_path=self.session_path,
                timestamp_str=self.timestamp_str,
            )
            self._update_session_metadata_file()
            self._can_evaluate = True

    @abstractmethod
    def evaluate(
            self,
            time_steps: Optional[int] = None,
            episodes: Optional[int] = None,
            **kwargs
    ):
        pass

    @abstractmethod
    def _get_latest_checkpoint(self):
        pass

    @classmethod
    @abstractmethod
    def load(cls):
        pass

    @abstractmethod
    def save(self):
        self._agent.save(self.session_path)

    @abstractmethod
    def export(self):
        pass


class DeterministicAgentSessionABC(AgentSessionABC):
    @abstractmethod
    def __init__(
            self,
            training_config_path,
            lay_down_config_path
    ):
        self._training_config_path = training_config_path
        self._lay_down_config_path = lay_down_config_path
        self._env: Primaite
        self._agent = None

    @abstractmethod
    def _setup(self):
        pass

    @abstractmethod
    def _get_latest_checkpoint(self):
        pass

    def learn(
            self,
            time_steps: Optional[int] = None,
            episodes: Optional[int] = None
    ):
        _LOGGER.warning("Deterministic agents cannot learn")

    @abstractmethod
    def evaluate(
            self,
            time_steps: Optional[int] = None,
            episodes: Optional[int] = None
    ):
        pass

    @classmethod
    @abstractmethod
    def load(cls):
        pass

    @abstractmethod
    def save(self):
        pass

    @abstractmethod
    def export(self):
        pass
