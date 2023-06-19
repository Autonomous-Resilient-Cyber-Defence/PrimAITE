from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Final, Optional, Union, Dict
from uuid import uuid4

from primaite import getLogger, SESSIONS_DIR
from primaite.agents.agent import AgentSessionABC
from primaite.agents.rllib import RLlibAgent
from primaite.agents.sb3 import SB3Agent
from primaite.common.enums import AgentFramework, RedAgentIdentifier, \
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
            lay_down_config_path: Union[str, Path],
            auto: bool = True
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

        self._auto: bool = auto
        self._agent_session: AgentSessionABC = None  # noqa

        if self._auto:
            self.setup()
            self.learn()

    def setup(self):
        if self._training_config.agent_framework == AgentFramework.NONE:
            if self._training_config.red_agent_identifier == RedAgentIdentifier.RANDOM:
                # Stochastic Random Agent
                raise NotImplementedError

            elif self._training_config.red_agent_identifier == RedAgentIdentifier.HARDCODED:
                if self._training_config.action_type == ActionType.NODE:
                    # Deterministic Hardcoded Agent with Node Action Space
                    raise NotImplementedError

                elif self._training_config.action_type == ActionType.ACL:
                    # Deterministic Hardcoded Agent with ACL Action Space
                    raise NotImplementedError

                elif self._training_config.action_type == ActionType.ANY:
                    # Deterministic Hardcoded Agent with ANY Action Space
                    raise NotImplementedError

                else:
                    # Invalid RedAgentIdentifier ActionType combo
                    pass

            else:
                # Invalid AgentFramework RedAgentIdentifier combo
                pass

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
            pass

    def learn(
            self,
            time_steps: Optional[int] = None,
            episodes: Optional[int] = None,
            **kwargs
    ):
        if not self._training_config.session_type == SessionType.EVALUATION:
            self._agent_session.learn(time_steps, episodes, **kwargs)

    def evaluate(
            self,
            time_steps: Optional[int] = None,
            episodes: Optional[int] = None,
            **kwargs
    ):
        if not self._training_config.session_type == SessionType.TRAINING:
            self._agent_session.evaluate(time_steps, episodes, **kwargs)
