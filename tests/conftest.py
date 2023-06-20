# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Final, Union

import pandas as pd

from primaite.environment.primaite_env import Primaite
from primaite.main import _get_session_path, _write_session_metadata_file

ACTION_SPACE_NODE_VALUES = 1
ACTION_SPACE_NODE_ACTION_VALUES = 1


def _get_temp_session_path(session_timestamp: datetime) -> Path:
    """
    Get a temp directory session path the test session will output to.

    :param session_timestamp: This is the datetime that the session started.
    :return: The session directory path.
    """
    date_dir = session_timestamp.strftime("%Y-%m-%d")
    session_dir = session_timestamp.strftime("%Y-%m-%d_%H-%M-%S")
    session_path = Path(tempfile.gettempdir()) / "primaite" / date_dir / session_dir
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
        transaction_list=[],
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


def compare_file_content(output_a_file_path: str, output_b_file_path: str):
    """Function used to check if output of both given files are the same."""
    with open(output_a_file_path) as f1:
        with open(output_b_file_path) as f2:
            f1_content = f1.read()
            f2_content = f2.read()

            # check that both files are not empty and are matching
            if len(f1_content) > 0 and len(f2_content) > 0 and f1_content == f2_content:
                # both files have the same content
                return True
            # both files have different content
            print(
                f"{output_a_file_path} and {output_b_file_path} has different contents"
            )

            return False


def compare_transaction_file(output_a_file_path: str, output_b_file_path: str):
    """Function used to check if contents of transaction files are the same."""
    # load output a file
    data_a = pd.read_csv(output_a_file_path)

    # load output b file
    data_b = pd.read_csv(output_b_file_path)

    # remove the time stamp column
    data_a.drop("Timestamp", inplace=True, axis=1)
    data_b.drop("Timestamp", inplace=True, axis=1)

    # if the comparison is empty, both files are the same i.e. True
    return data_a.compare(data_b).empty


class TestSession:
    """Class that contains session values."""

    def __init__(self, training_config_path, laydown_config_path):
        self.session_timestamp: Final[datetime] = datetime.now()
        self.session_dir = _get_session_path(self.session_timestamp)
        self.timestamp_str = self.session_timestamp.strftime("%Y-%m-%d_%H-%M-%S")
        self.transaction_list = []

        print(f"The output directory for this session is: {self.session_dir}")

        self.env = Primaite(
            training_config_path=training_config_path,
            lay_down_config_path=laydown_config_path,
            transaction_list=self.transaction_list,
            session_path=self.session_dir,
            timestamp_str=self.timestamp_str,
        )

        print("Writing Session Metadata file...")

        _write_session_metadata_file(
            session_dir=self.session_dir,
            uuid="test",
            session_timestamp=self.session_timestamp,
            env=self.env,
        )
