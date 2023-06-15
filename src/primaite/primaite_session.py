from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Final, Optional, Union
from uuid import uuid4

from primaite import getLogger, SESSIONS_DIR
from primaite.common.enums import AgentFramework, RedAgentIdentifier, \
    ActionType
from primaite.config.training_config import TrainingConfig
from primaite.environment.primaite_env import Primaite

_LOGGER = getLogger(__name__)


def _get_session_path(session_timestamp: datetime) -> Path:
    """
    Get the directory path the session will output to.

    This is set in the format of:
        ~/primaite/sessions/<yyyy-mm-dd>/<yyyy-mm-dd>_<hh-mm-ss>.

    :param session_timestamp: This is the datetime that the session started.
    :return: The session directory path.
    """
    date_dir = session_timestamp.strftime("%Y-%m-%d")
    session_dir = session_timestamp.strftime("%Y-%m-%d_%H-%M-%S")
    session_path = SESSIONS_DIR / date_dir / session_dir
    session_path.mkdir(exist_ok=True, parents=True)
    _LOGGER.debug(f"Created PrimAITE Session path: {session_path}")

    return session_path


class PrimaiteSession:

    def __init__(
            self,
            training_config_path: Union[str, Path],
            lay_down_config_path: Union[str, Path],
            auto: bool = True
    ):
        if not isinstance(training_config_path, Path):
            training_config_path = Path(training_config_path)
        self._training_config_path: Final[Union[Path]] = training_config_path

        if not isinstance(lay_down_config_path, Path):
            lay_down_config_path = Path(lay_down_config_path)
        self._lay_down_config_path: Final[Union[Path]] = lay_down_config_path

        self._auto: Final[bool] = auto

        self._uuid: str = str(uuid4())
        self._session_timestamp: Final[datetime] = datetime.now()
        self._session_path: Final[Path] = _get_session_path(
            self._session_timestamp
        )
        self._timestamp_str: Final[str] = self._session_timestamp.strftime(
            "%Y-%m-%d_%H-%M-%S")
        self._metadata_path = self._session_path / "session_metadata.json"


        self._env  = None
        self._training_config: TrainingConfig
        self._can_learn: bool = False
        _LOGGER.debug("")

        if self._auto:
            self.setup()
            self.learn()

    @property
    def uuid(self):
        """The session UUID."""
        return self._uuid

    def _setup_primaite_env(self, transaction_list: Optional[list] = None):
        if not transaction_list:
            transaction_list = []
        self._env: Primaite = Primaite(
            training_config_path=self._training_config_path,
            lay_down_config_path=self._lay_down_config_path,
            transaction_list=transaction_list,
            session_path=self._session_path,
            timestamp_str=self._timestamp_str
        )
        self._training_config: TrainingConfig = self._env.training_config

    def _write_session_metadata_file(self):
        """
        Write the ``session_metadata.json`` file.

        Creates a ``session_metadata.json`` in the ``session_dir`` directory
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
            "uuid": self._uuid,
            "start_datetime": self._session_timestamp.isoformat(),
            "end_datetime": None,
            "total_episodes": None,
            "total_time_steps": None,
            "env": {
                "training_config": self._env.training_config.to_dict(
                    json_serializable=True
                ),
                "lay_down_config": self._env.lay_down_config,
            },
        }
        _LOGGER.debug(f"Writing Session Metadata file: {self._metadata_path}")
        with open(self._metadata_path, "w") as file:
            json.dump(metadata_dict, file)

    def _update_session_metadata_file(self):
        """
        Update the ``session_metadata.json`` file.

        Updates the `session_metadata.json`` in the ``session_dir`` directory
        with the following key/value pairs:

        - end_datetime: NULL.
        - total_episodes: NULL.
        - total_time_steps: NULL.
        """
        with open(self._metadata_path, "r") as file:
            metadata_dict = json.load(file)

        metadata_dict["end_datetime"] = datetime.now().isoformat()
        metadata_dict["total_episodes"] = self._env.episode_count
        metadata_dict["total_time_steps"] = self._env.total_step_count

        _LOGGER.debug(f"Updating Session Metadata file: {self._metadata_path}")
        with open(self._metadata_path, "w") as file:
            json.dump(metadata_dict, file)

    def setup(self):
        self._setup_primaite_env()
        self._can_learn = True
        pass

    def learn(
            self,
            time_steps: Optional[int],
            episodes: Optional[int],
            iterations: Optional[int],
            **kwargs
    ):
        if self._can_learn:
            # Run environment against an agent
            if self._training_config.agent_framework == AgentFramework.NONE:
                if self._training_config.red_agent_identifier == RedAgentIdentifier.RANDOM:
                    # Stochastic Random Agent
                    run_generic(env=env, config_values=config_values)

                elif self._training_config.red_agent_identifier == RedAgentIdentifier.HARDCODED:
                    if self._training_config.action_type == ActionType.NODE:
                        # Deterministic Hardcoded Agent with Node Action Space
                        pass

                    elif self._training_config.action_type == ActionType.ACL:
                        # Deterministic Hardcoded Agent with ACL Action Space
                        pass

                    elif self._training_config.action_type == ActionType.ANY:
                        # Deterministic Hardcoded Agent with ANY Action Space
                        pass

                    else:
                        # Invalid RedAgentIdentifier ActionType combo
                        pass

                else:
                    # Invalid AgentFramework RedAgentIdentifier combo
                    pass

            elif self._training_config.agent_framework == AgentFramework.SB3:
                if self._training_config.red_agent_identifier == RedAgentIdentifier.PPO:
                    # Stable Baselines3/Proximal Policy Optimization
                    run_stable_baselines3_ppo(
                        env=env,
                        config_values=config_values,
                        session_path=session_dir,
                        timestamp_str=timestamp_str,
                    )

                elif self._training_config.red_agent_identifier == RedAgentIdentifier.A2C:
                    # Stable Baselines3/Advantage Actor Critic
                    run_stable_baselines3_a2c(
                        env=env,
                        config_values=config_values,
                        session_path=session_dir,
                        timestamp_str=timestamp_str,
                    )

                else:
                    # Invalid AgentFramework RedAgentIdentifier combo
                    pass

            elif self._training_config.agent_framework == AgentFramework.RLLIB:
                if self._training_config.red_agent_identifier == RedAgentIdentifier.PPO:
                    # Ray RLlib/Proximal Policy Optimization
                    pass

                elif self._training_config.red_agent_identifier == RedAgentIdentifier.A2C:
                    # Ray RLlib/Advantage Actor Critic
                    pass

                else:
                    # Invalid AgentFramework RedAgentIdentifier combo
                    pass
            else:
                # Invalid AgentFramework
                pass

            print("Session finished")
            _LOGGER.debug("Session finished")

            print("Saving transaction logs...")
            write_transaction_to_file(
                transaction_list=transaction_list,
                session_path=session_dir,
                timestamp_str=timestamp_str,
            )

            print("Updating Session Metadata file...")
            _update_session_metadata_file(session_dir=session_dir, env=env)

            print("Finished")
            _LOGGER.debug("Finished")

    def evaluate(
            self,
            time_steps: Optional[int],
            episodes: Optional[int],
            **kwargs
    ):
        pass

    def export(self):
        pass

    @classmethod
    def import_agent(
            cls,
            gent_path: str,
            training_config_path: str,
            lay_down_config_path: str
    ) -> PrimaiteSession:
        session = PrimaiteSession(training_config_path, lay_down_config_path)

        # Reset the UUID
        session._uuid = ""

        return session
