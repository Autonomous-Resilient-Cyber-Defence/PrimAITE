from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Final, Optional, Union, Dict
from uuid import uuid4

from primaite import getLogger, SESSIONS_DIR
from primaite.agents.agent import AgentSessionABC
from primaite.agents.hardcoded_acl import HardCodedACLAgent
from primaite.agents.hardcoded_node import HardCodedNodeAgent
from primaite.agents.rllib import RLlibAgent
from primaite.agents.sb3 import SB3Agent
from primaite.agents.simple import DoNothingACLAgent, DoNothingNodeAgent, \
    RandomAgent, DummyAgent
from primaite.common.enums import AgentFramework, AgentIdentifier, \
    ActionType, SessionType
from primaite.config import lay_down_config, training_config
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
    session_path = session_timestamp.strftime("%Y-%m-%d_%H-%M-%S")
    session_path = SESSIONS_DIR / date_dir / session_path
    session_path.mkdir(exist_ok=True, parents=True)
    _LOGGER.debug(f"Created PrimAITE Session path: {session_path}")

    return session_path


class PrimaiteSession:

    def __init__(
            self,
            training_config_path: Union[str, Path],
            lay_down_config_path: Union[str, Path]
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

        self._agent_session: AgentSessionABC = None  # noqa

    def setup(self):
        if self._training_config.agent_framework == AgentFramework.CUSTOM:
            if self._training_config.agent_identifier == AgentIdentifier.HARDCODED:
                if self._training_config.action_type == ActionType.NODE:
                    # Deterministic Hardcoded Agent with Node Action Space
                    self._agent_session = HardCodedNodeAgent(
                        self._training_config_path,
                        self._lay_down_config_path
                    )

                elif self._training_config.action_type == ActionType.ACL:
                    # Deterministic Hardcoded Agent with ACL Action Space
                    self._agent_session = HardCodedACLAgent(
                        self._training_config_path,
                        self._lay_down_config_path
                    )

                elif self._training_config.action_type == ActionType.ANY:
                    # Deterministic Hardcoded Agent with ANY Action Space
                    raise NotImplementedError

                else:
                    # Invalid AgentIdentifier ActionType combo
                    raise ValueError

            elif self._training_config.agent_identifier == AgentIdentifier.DO_NOTHING:
                if self._training_config.action_type == ActionType.NODE:
                    self._agent_session = DoNothingNodeAgent(
                        self._training_config_path,
                        self._lay_down_config_path
                    )

                elif self._training_config.action_type == ActionType.ACL:
                    # Deterministic Hardcoded Agent with ACL Action Space
                    self._agent_session = DoNothingACLAgent(
                        self._training_config_path,
                        self._lay_down_config_path
                    )

                elif self._training_config.action_type == ActionType.ANY:
                    # Deterministic Hardcoded Agent with ANY Action Space
                    raise NotImplementedError

                else:
                    # Invalid AgentIdentifier ActionType combo
                    raise ValueError

            elif self._training_config.agent_identifier == AgentIdentifier.RANDOM:
                self._agent_session = RandomAgent(
                    self._training_config_path,
                    self._lay_down_config_path
                )
            elif self._training_config.agent_identifier == AgentIdentifier.DUMMY:
                self._agent_session = DummyAgent(
                    self._training_config_path,
                    self._lay_down_config_path
                )

            else:
                # Invalid AgentFramework AgentIdentifier combo
                raise ValueError

        elif self._training_config.agent_framework == AgentFramework.SB3:
            # Stable Baselines3 Agent
            self._agent_session = SB3Agent(
                self._training_config_path,
                self._lay_down_config_path
            )

        elif self._training_config.agent_framework == AgentFramework.RLLIB:
            # Ray RLlib Agent
            self._agent_session = RLlibAgent(
                self._training_config_path,
                self._lay_down_config_path
            )

        else:
            # Invalid AgentFramework
            raise ValueError

    def learn(
            self,
            time_steps: Optional[int] = None,
            episodes: Optional[int] = None,
            **kwargs
    ):
        if not self._training_config.session_type == SessionType.EVAL:
            self._agent_session.learn(time_steps, episodes, **kwargs)

    def evaluate(
            self,
            time_steps: Optional[int] = None,
            episodes: Optional[int] = None,
            **kwargs
    ):
        if not self._training_config.session_type == SessionType.TRAIN:
            self._agent_session.evaluate(time_steps, episodes, **kwargs)
