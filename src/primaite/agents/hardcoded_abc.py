# Crown Owned Copyright (C) Dstl 2023. DEFCON 703. Shared in confidence.
import time
from abc import abstractmethod
from pathlib import Path
from typing import Any, Optional, Union

import numpy as np

from primaite import getLogger
from primaite.agents.agent_abc import AgentSessionABC
from primaite.environment.primaite_env import Primaite

_LOGGER = getLogger(__name__)


class HardCodedAgentSessionABC(AgentSessionABC):
    """
    An Agent Session ABC for evaluation deterministic agents.

    This class cannot be directly instantiated and must be inherited from with all implemented abstract methods
    implemented.
    """

    def __init__(
        self,
        training_config_path: Optional[Union[str, Path]] = "",
        lay_down_config_path: Optional[Union[str, Path]] = "",
        session_path: Optional[Union[str, Path]] = None,
    ) -> None:
        """
        Initialise a hardcoded agent session.

        :param training_config_path: YAML file containing configurable items defined in
            `primaite.config.training_config.TrainingConfig`
        :type training_config_path: Union[path, str]
        :param lay_down_config_path: YAML file containing configurable items for generating network laydown.
        :type lay_down_config_path: Union[path, str]
        """
        super().__init__(training_config_path, lay_down_config_path, session_path)
        self._setup()

    def _setup(self) -> None:
        self._env: Primaite = Primaite(
            training_config_path=self._training_config_path,
            lay_down_config_path=self._lay_down_config_path,
            session_path=self.session_path,
            timestamp_str=self.timestamp_str,
        )
        super()._setup()
        self._can_learn = False
        self._can_evaluate = True

    def _save_checkpoint(self) -> None:
        pass

    def _get_latest_checkpoint(self) -> None:
        pass

    def learn(
        self,
        **kwargs: Any,
    ) -> None:
        """
        Train the agent.

        :param kwargs: Any agent-specific key-word args to be passed.
        """
        _LOGGER.warning("Deterministic agents cannot learn")

    @abstractmethod
    def _calculate_action(self, obs: np.ndarray) -> None:
        pass

    def evaluate(
        self,
        **kwargs: Any,
    ) -> None:
        """
        Evaluate the agent.

        :param kwargs: Any agent-specific key-word args to be passed.
        """
        self._env.set_as_eval()  # noqa
        self.is_eval = True

        time_steps = self._training_config.num_eval_steps
        episodes = self._training_config.num_eval_episodes

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
    def load(cls, path: Union[str, Path] = None) -> None:
        """Load an agent from file."""
        _LOGGER.warning("Deterministic agents cannot be loaded")

    def save(self) -> None:
        """Save the agent."""
        _LOGGER.warning("Deterministic agents cannot be saved")

    def export(self) -> None:
        """Export the agent to transportable file format."""
        _LOGGER.warning("Deterministic agents cannot be exported")
