# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
"""Main entry point to PrimAITE. Configure training/evaluation experiments and input/output."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Final, Optional, Tuple, Union

from primaite import getLogger
from primaite.agents.agent_abc import AgentSessionABC
from primaite.agents.hardcoded_acl import HardCodedACLAgent
from primaite.agents.hardcoded_node import HardCodedNodeAgent
from primaite.agents.rllib import RLlibAgent
from primaite.agents.sb3 import SB3Agent
from primaite.agents.simple import DoNothingACLAgent, DoNothingNodeAgent, DummyAgent, RandomAgent
from primaite.common.enums import ActionType, AgentFramework, AgentIdentifier, SessionType
from primaite.config import lay_down_config, training_config
from primaite.config.training_config import TrainingConfig
from primaite.utils.session_metadata_parser import parse_session_metadata
from primaite.utils.session_output_reader import all_transactions_dict, av_rewards_dict

_LOGGER = getLogger(__name__)


class PrimaiteSession:
    """
    The PrimaiteSession class.

    Provides a single learning and evaluation entry point for all training and lay down configurations.
    """

    def __init__(
        self,
        training_config_path: Optional[Union[str, Path]] = "",
        lay_down_config_path: Optional[Union[str, Path]] = "",
        session_path: Optional[Union[str, Path]] = None,
        legacy_training_config: bool = False,
        legacy_lay_down_config: bool = False,
    ) -> None:
        """
        The PrimaiteSession constructor.

        :param training_config_path: YAML file containing configurable items defined in
            `primaite.config.training_config.TrainingConfig`
        :type training_config_path: Union[path, str]
        :param lay_down_config_path: YAML file containing configurable items for generating network laydown.
        :type lay_down_config_path: Union[path, str]
        :param session_path: directory path of the session to load
        :param legacy_training_config: True if the training config file is a legacy file from PrimAITE < 2.0,
            otherwise False.
        :param legacy_lay_down_config: True if the lay_down config file is a legacy file from PrimAITE < 2.0,
            otherwise False.
        """
        self._agent_session: AgentSessionABC = None  # noqa
        self.session_path: Path = session_path  # noqa
        self.timestamp_str: str = None  # noqa
        self.learning_path: Path = None  # noqa
        self.evaluation_path: Path = None  # noqa
        self.legacy_training_config = legacy_training_config
        self.legacy_lay_down_config = legacy_lay_down_config

        # check if session path is provided
        if session_path is not None:
            # set load_session to true
            self.is_load_session = True
            if not isinstance(session_path, Path):
                session_path = Path(session_path)

            # if a session path is provided, load it
            if not session_path.exists():
                raise Exception(f"Session could not be loaded. Path does not exist: {session_path}")

            md_dict, training_config_path, lay_down_config_path = parse_session_metadata(session_path)

        if not isinstance(training_config_path, Path):
            training_config_path = Path(training_config_path)
        self._training_config_path: Final[Union[Path, str]] = training_config_path
        self._training_config: Final[TrainingConfig] = training_config.load(
            self._training_config_path, legacy_training_config
        )

        if not isinstance(lay_down_config_path, Path):
            lay_down_config_path = Path(lay_down_config_path)
        self._lay_down_config_path: Final[Union[Path, str]] = lay_down_config_path
        self._lay_down_config: Dict = lay_down_config.load(self._lay_down_config_path, legacy_lay_down_config)  # noqa

    def setup(self) -> None:
        """Performs the session setup."""
        if self._training_config.agent_framework == AgentFramework.CUSTOM:
            _LOGGER.debug(f"PrimaiteSession Setup: Agent Framework = {AgentFramework.CUSTOM}")
            if self._training_config.agent_identifier == AgentIdentifier.HARDCODED:
                _LOGGER.debug(f"PrimaiteSession Setup: Agent Identifier =" f" {AgentIdentifier.HARDCODED}")
                if self._training_config.action_type == ActionType.NODE:
                    # Deterministic Hardcoded Agent with Node Action Space
                    self._agent_session = HardCodedNodeAgent(
                        self._training_config_path, self._lay_down_config_path, self.session_path
                    )

                elif self._training_config.action_type == ActionType.ACL:
                    # Deterministic Hardcoded Agent with ACL Action Space
                    self._agent_session = HardCodedACLAgent(
                        self._training_config_path, self._lay_down_config_path, self.session_path
                    )

                elif self._training_config.action_type == ActionType.ANY:
                    # Deterministic Hardcoded Agent with ANY Action Space
                    raise NotImplementedError

                else:
                    # Invalid AgentIdentifier ActionType combo
                    raise ValueError

            elif self._training_config.agent_identifier == AgentIdentifier.DO_NOTHING:
                _LOGGER.debug(f"PrimaiteSession Setup: Agent Identifier =" f" {AgentIdentifier.DO_NOTHING}")
                if self._training_config.action_type == ActionType.NODE:
                    self._agent_session = DoNothingNodeAgent(
                        self._training_config_path, self._lay_down_config_path, self.session_path
                    )

                elif self._training_config.action_type == ActionType.ACL:
                    # Deterministic Hardcoded Agent with ACL Action Space
                    self._agent_session = DoNothingACLAgent(
                        self._training_config_path, self._lay_down_config_path, self.session_path
                    )

                elif self._training_config.action_type == ActionType.ANY:
                    # Deterministic Hardcoded Agent with ANY Action Space
                    raise NotImplementedError

                else:
                    # Invalid AgentIdentifier ActionType combo
                    raise ValueError

            elif self._training_config.agent_identifier == AgentIdentifier.RANDOM:
                _LOGGER.debug(f"PrimaiteSession Setup: Agent Identifier =" f" {AgentIdentifier.RANDOM}")
                self._agent_session = RandomAgent(
                    self._training_config_path, self._lay_down_config_path, self.session_path
                )
            elif self._training_config.agent_identifier == AgentIdentifier.DUMMY:
                _LOGGER.debug(f"PrimaiteSession Setup: Agent Identifier =" f" {AgentIdentifier.DUMMY}")
                self._agent_session = DummyAgent(
                    self._training_config_path, self._lay_down_config_path, self.session_path
                )

            else:
                # Invalid AgentFramework AgentIdentifier combo
                raise ValueError

        elif self._training_config.agent_framework == AgentFramework.SB3:
            _LOGGER.debug(f"PrimaiteSession Setup: Agent Framework = {AgentFramework.SB3}")
            # Stable Baselines3 Agent
            self._agent_session = SB3Agent(
                self._training_config_path,
                self._lay_down_config_path,
                self.session_path,
                self.legacy_training_config,
                self.legacy_lay_down_config,
            )

        elif self._training_config.agent_framework == AgentFramework.RLLIB:
            _LOGGER.debug(f"PrimaiteSession Setup: Agent Framework = {AgentFramework.RLLIB}")
            # Ray RLlib Agent
            self._agent_session = RLlibAgent(
                self._training_config_path,
                self._lay_down_config_path,
                self.session_path,
                self.legacy_training_config,
                self.legacy_lay_down_config,
            )

        else:
            # Invalid AgentFramework
            raise ValueError

        self.session_path: Path = self._agent_session.session_path
        self.timestamp_str: str = self._agent_session.timestamp_str
        self.learning_path: Path = self._agent_session.learning_path
        self.evaluation_path: Path = self._agent_session.evaluation_path

    def learn(
        self,
        **kwargs: Any,
    ) -> None:
        """
        Train the agent.

        :param kwargs: Any agent-framework specific key word args.
        """
        if not self._training_config.session_type == SessionType.EVAL:
            self._agent_session.learn(**kwargs)

    def evaluate(
        self,
        **kwargs: Any,
    ) -> None:
        """
        Evaluate the agent.

        :param kwargs: Any agent-framework specific key word args.
        """
        if not self._training_config.session_type == SessionType.TRAIN:
            self._agent_session.evaluate(**kwargs)

    def close(self) -> None:
        """Closes the agent."""
        self._agent_session.close()

    def learn_av_reward_per_episode_dict(self) -> Dict[int, float]:
        """Get the learn av reward per episode from file."""
        csv_file = f"average_reward_per_episode_{self.timestamp_str}.csv"
        return av_rewards_dict(self.learning_path / csv_file)

    def eval_av_reward_per_episode_dict(self) -> Dict[int, float]:
        """Get the eval av reward per episode from file."""
        csv_file = f"average_reward_per_episode_{self.timestamp_str}.csv"
        return av_rewards_dict(self.evaluation_path / csv_file)

    def learn_all_transactions_dict(self) -> Dict[Tuple[int, int], Dict[str, Any]]:
        """Get the learn all transactions from file."""
        csv_file = f"all_transactions_{self.timestamp_str}.csv"
        return all_transactions_dict(self.learning_path / csv_file)

    def eval_all_transactions_dict(self) -> Dict[Tuple[int, int], Dict[str, Any]]:
        """Get the eval all transactions from file."""
        csv_file = f"all_transactions_{self.timestamp_str}.csv"
        return all_transactions_dict(self.evaluation_path / csv_file)

    def metadata_file_as_dict(self) -> Dict[str, Any]:
        """Read the session_metadata.json file and return as a dict."""
        with open(self.session_path / "session_metadata.json", "r") as file:
            return json.load(file)
