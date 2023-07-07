# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
import datetime
import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Union
from unittest.mock import patch

import pytest

from primaite import getLogger
from primaite.common.enums import AgentIdentifier
from primaite.environment.primaite_env import Primaite
from primaite.primaite_session import PrimaiteSession
from primaite.utils.session_output_reader import av_rewards_dict
from tests.mock_and_patch.get_session_path_mock import get_temp_session_path

ACTION_SPACE_NODE_VALUES = 1
ACTION_SPACE_NODE_ACTION_VALUES = 1

_LOGGER = getLogger(__name__)


class TempPrimaiteSession(PrimaiteSession):
    """
    A temporary PrimaiteSession class.

    Uses context manager for deletion of files upon exit.
    """

    def __init__(
        self,
        training_config_path: Union[str, Path],
        lay_down_config_path: Union[str, Path],
    ):
        super().__init__(training_config_path, lay_down_config_path)
        self.setup()

    def learn_av_reward_per_episode(self) -> Dict[int, float]:
        """Get the learn av reward per episode from file."""
        csv_file = f"average_reward_per_episode_{self.timestamp_str}.csv"
        return av_rewards_dict(self.learning_path / csv_file)

    def eval_av_reward_per_episode_csv(self) -> Dict[int, float]:
        """Get the eval av reward per episode from file."""
        csv_file = f"average_reward_per_episode_{self.timestamp_str}.csv"
        return av_rewards_dict(self.evaluation_path / csv_file)

    @property
    def env(self) -> Primaite:
        """Direct access to the env for ease of testing."""
        return self._agent_session._env  # noqa

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        shutil.rmtree(self.session_path)
        _LOGGER.debug(f"Deleted temp session directory: {self.session_path}")


@pytest.fixture
def temp_primaite_session(request):
    """
    Provides a temporary PrimaiteSession instance.

    It's temporary as it uses a temporary directory as the session path.

    To use this fixture you need to:

    - parametrize your test function with:

      - "temp_primaite_session"
      - [[path to training config, path to lay down config]]
    - Include the temp_primaite_session fixture as a param in your test
    function.
    - use the temp_primaite_session as a context manager assigning is the
    name 'session'.

    .. code:: python

        from primaite.config.lay_down_config import dos_very_basic_config_path
        from primaite.config.training_config import main_training_config_path
        @pytest.mark.parametrize(
            "temp_primaite_session",
            [
                [main_training_config_path(), dos_very_basic_config_path()]
            ],
            indirect=True
        )
        def test_primaite_session(temp_primaite_session):
            with temp_primaite_session as session:
                # Learning outputs are saved in session.learning_path
                session.learn()

                # Evaluation outputs are saved in session.evaluation_path
                session.evaluate()

                # To ensure that all files are written, you must call .close()
                session.close()

                # If you need to inspect any session outputs, it must be done
                # inside the context manager

            # Now that we've exited the context manager, the
            # session.session_path directory and its contents are deleted
    """
    training_config_path = request.param[0]
    lay_down_config_path = request.param[1]
    with patch("primaite.agents.agent.get_session_path", get_temp_session_path) as mck:
        mck.session_timestamp = datetime.now()

        return TempPrimaiteSession(training_config_path, lay_down_config_path)


@pytest.fixture
def temp_session_path() -> Path:
    """
    Get a temp directory session path the test session will output to.

    :return: The session directory path.
    """
    session_timestamp = datetime.now()
    date_dir = session_timestamp.strftime("%Y-%m-%d")
    session_path = session_timestamp.strftime("%Y-%m-%d_%H-%M-%S")
    session_path = Path(tempfile.gettempdir()) / "primaite" / date_dir / session_path
    session_path.mkdir(exist_ok=True, parents=True)

    return session_path


def _get_primaite_env_from_config(
    training_config_path: Union[str, Path],
    lay_down_config_path: Union[str, Path],
    temp_session_path,
):
    """Takes a config path and returns the created instance of Primaite."""
    session_timestamp: datetime = datetime.now()
    session_path = temp_session_path(session_timestamp)

    timestamp_str = session_timestamp.strftime("%Y-%m-%d_%H-%M-%S")
    env = Primaite(
        training_config_path=training_config_path,
        lay_down_config_path=lay_down_config_path,
        session_path=session_path,
        timestamp_str=timestamp_str,
    )
    config_values = env.training_config
    config_values.num_steps = env.episode_steps

    # TOOD: This needs t be refactored to happen outside. Should be part of
    # a main Session class.
    if env.training_config.agent_identifier is AgentIdentifier.RANDOM:
        run_generic(env, config_values)

    return env


def run_generic(env, config_values):
    """Run against a generic agent."""
    # Reset the environment at the start of the episode
    # env.reset()
    for episode in range(0, config_values.num_episodes):
        for step in range(0, config_values.num_steps):
            # Send the observation space to the agent to get an action
            # TEMP - random action for now
            # action = env.blue_agent_action(obs)
            # action = env.action_space.sample()
            action = 0

            # Run the simulation step on the live environment
            obs, reward, done, info = env.step(action)

            # Break if done is True
            if done:
                break

            # Introduce a delay between steps
            time.sleep(config_values.time_delay / 1000)

        # Reset the environment at the end of the episode
        # env.reset()

    # env.close()
