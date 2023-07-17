# Crown Owned Copyright (C) Dstl 2023. DEFCON 703. Shared in confidence.
"""Main entry point to PrimAITE. Configure training/evaluation experiments and input/output."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Final, Optional, Union

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
    ):
        """
        The PrimaiteSession constructor.

        :param training_config_path: YAML file containing configurable items defined in
            `primaite.config.training_config.TrainingConfig`
        :type training_config_path: Union[path, str]
        :param lay_down_config_path: YAML file containing configurable items for generating network laydown.
        :type lay_down_config_path: Union[path, str]
        :param session_path: directory path of the session to load
        """
        self._agent_session: AgentSessionABC = None  # noqa
        self.session_path: Path = session_path  # noqa
        self.timestamp_str: str = None  # noqa
        self.learning_path: Path = None  # noqa
        self.evaluation_path: Path = None  # noqa

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
        self._training_config: Final[TrainingConfig] = training_config.load(self._training_config_path)

        if not isinstance(lay_down_config_path, Path):
            lay_down_config_path = Path(lay_down_config_path)
        self._lay_down_config_path: Final[Union[Path, str]] = lay_down_config_path
        self._lay_down_config: Dict = lay_down_config.load(self._lay_down_config_path)

    def setup(self):
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
            self._agent_session = SB3Agent(self._training_config_path, self._lay_down_config_path, self.session_path)

        elif self._training_config.agent_framework == AgentFramework.RLLIB:
            _LOGGER.debug(f"PrimaiteSession Setup: Agent Framework = {AgentFramework.RLLIB}")
            # Ray RLlib Agent
            self._agent_session = RLlibAgent(self._training_config_path, self._lay_down_config_path, self.session_path)

        else:
            # Invalid AgentFramework
            raise ValueError

        self.session_path: Path = self._agent_session.session_path
        self.timestamp_str: str = self._agent_session.timestamp_str
        self.learning_path: Path = self._agent_session.learning_path
        self.evaluation_path: Path = self._agent_session.evaluation_path

    def learn(
        self,
        **kwargs,
    ):
        """
        Train the agent.

        :param kwargs: Any agent-framework specific key word args.
        """
        if not self._training_config.session_type == SessionType.EVAL:
            self._agent_session.learn(**kwargs)

    def evaluate(
        self,
        **kwargs,
    ):
        """
        Evaluate the agent.

        :param kwargs: Any agent-framework specific key word args.
        """
        if not self._training_config.session_type == SessionType.TRAIN:
            self._agent_session.evaluate(**kwargs)

    def close(self):
        """Closes the agent."""
        self._agent_session.close()
