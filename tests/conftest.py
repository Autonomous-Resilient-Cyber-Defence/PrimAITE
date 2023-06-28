# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Union

from primaite.environment.primaite_env import Primaite

ACTION_SPACE_NODE_VALUES = 1
ACTION_SPACE_NODE_ACTION_VALUES = 1


def _get_temp_session_path(session_timestamp: datetime) -> Path:
    """
    Get a temp directory session path the test session will output to.

    :param session_timestamp: This is the datetime that the session started.
    :return: The session directory path.
    """
    date_dir = session_timestamp.strftime("%Y-%m-%d")
    session_path = session_timestamp.strftime("%Y-%m-%d_%H-%M-%S")
    session_path = Path(tempfile.gettempdir()) / "primaite" / date_dir / session_path
    session_path.mkdir(exist_ok=True, parents=True)

    return session_path


def _get_primaite_env_from_config(
    training_config_path: Union[str, Path], lay_down_config_path: Union[str, Path]
):
    """Takes a config path and returns the created instance of Primaite."""
    session_timestamp: datetime = datetime.now()
    session_path = _get_temp_session_path(session_timestamp)

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
    if env.training_config.agent_identifier == "GENERIC":
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
