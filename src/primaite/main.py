# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""
The main PrimAITE session runner module.

TODO: This will eventually be refactored out into a proper Session class.
TODO: The passing about of session_dir and timestamp_str is temporary and
    will be cleaned up once we move to a proper Session class.
"""
import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Final, Union
from uuid import uuid4

from stable_baselines3 import A2C, PPO
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.on_policy_algorithm import OnPolicyAlgorithm
from stable_baselines3.ppo import MlpPolicy as PPOMlp

from primaite import SESSIONS_DIR, getLogger
from primaite.config.training_config import TrainingConfig
from primaite.environment.primaite_env import Primaite
from primaite.transactions.transactions_to_file import write_transaction_to_file

_LOGGER = getLogger(__name__)


def run_generic(env: Primaite, config_values: TrainingConfig):
    """
    Run against a generic agent.

    :param env: An instance of
        :class:`~primaite.environment.primaite_env.Primaite`.
    :param config_values: An instance of
        :class:`~primaite.config.training_config.TrainingConfig`.
    """
    for episode in range(0, config_values.num_episodes):
        env.reset()
        for step in range(0, config_values.num_steps):
            # Send the observation space to the agent to get an action
            # TEMP - random action for now
            # action = env.blue_agent_action(obs)
            action = env.action_space.sample()

            # Run the simulation step on the live environment
            obs, reward, done, info = env.step(action)

            # Break if done is True
            if done:
                break

            # Introduce a delay between steps
            time.sleep(config_values.time_delay / 1000)

        # Reset the environment at the end of the episode

    env.close()


def run_stable_baselines3_ppo(
    env: Primaite, config_values: TrainingConfig, session_path: Path, timestamp_str: str
):
    """
    Run against a stable_baselines3 PPO agent.

    :param env: An instance of
        :class:`~primaite.environment.primaite_env.Primaite`.
    :param config_values: An instance of
        :class:`~primaite.config.training_config.TrainingConfig`.
    :param session_path: The directory path the session is writing to.
    :param timestamp_str: The session timestamp in the format:
        <yyyy-mm-dd>_<hh-mm-ss>.
    """
    if config_values.load_agent:
        try:
            agent = PPO.load(
                config_values.agent_load_file,
                env,
                verbose=0,
                n_steps=config_values.num_steps,
            )
        except Exception:
            print(
                "ERROR: Could not load agent at location: "
                + config_values.agent_load_file
            )
            _LOGGER.error("Could not load agent")
            _LOGGER.error("Exception occured", exc_info=True)
    else:
        agent = PPO(PPOMlp, env, verbose=0, n_steps=config_values.num_steps)

    if config_values.session_type == "TRAINING":
        # We're in a training session
        print("Starting training session...")
        _LOGGER.debug("Starting training session...")
        for episode in range(config_values.num_episodes):
            agent.learn(total_timesteps=config_values.num_steps)
        _save_agent(agent, session_path, timestamp_str)
    else:
        # Default to being in an evaluation session
        print("Starting evaluation session...")
        _LOGGER.debug("Starting evaluation session...")
        evaluate_policy(agent, env, n_eval_episodes=config_values.num_episodes)

    env.close()


def run_stable_baselines3_a2c(
    env: Primaite, config_values: TrainingConfig, session_path: Path, timestamp_str: str
):
    """
    Run against a stable_baselines3 A2C agent.

    :param env: An instance of
        :class:`~primaite.environment.primaite_env.Primaite`.
    :param config_values: An instance of
        :class:`~primaite.config.training_config.TrainingConfig`.
    param session_path: The directory path the session is writing to.
    :param timestamp_str: The session timestamp in the format:
        <yyyy-mm-dd>_<hh-mm-ss>.
    """
    if config_values.load_agent:
        try:
            agent = A2C.load(
                config_values.agent_load_file,
                env,
                verbose=0,
                n_steps=config_values.num_steps,
            )
        except Exception:
            print(
                "ERROR: Could not load agent at location: "
                + config_values.agent_load_file
            )
            _LOGGER.error("Could not load agent")
            _LOGGER.error("Exception occured", exc_info=True)
    else:
        agent = A2C("MlpPolicy", env, verbose=0, n_steps=config_values.num_steps)

    if config_values.session_type == "TRAINING":
        # We're in a training session
        print("Starting training session...")
        _LOGGER.debug("Starting training session...")
        for episode in range(config_values.num_episodes):
            agent.learn(total_timesteps=config_values.num_steps)
        _save_agent(agent, session_path, timestamp_str)
    else:
        # Default to being in an evaluation session
        print("Starting evaluation session...")
        _LOGGER.debug("Starting evaluation session...")
        evaluate_policy(agent, env, n_eval_episodes=config_values.num_episodes)

    env.close()


def _write_session_metadata_file(
    session_dir: Path, uuid: str, session_timestamp: datetime, env: Primaite
):
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
        "uuid": uuid,
        "start_datetime": session_timestamp.isoformat(),
        "end_datetime": None,
        "total_episodes": None,
        "total_time_steps": None,
        "env": {
            "training_config": env.training_config.to_dict(json_serializable=True),
            "lay_down_config": env.lay_down_config,
        },
    }
    filepath = session_dir / "session_metadata.json"
    _LOGGER.debug(f"Writing Session Metadata file: {filepath}")
    with open(filepath, "w") as file:
        json.dump(metadata_dict, file)


def _update_session_metadata_file(session_dir: Path, env: Primaite):
    """
    Update the ``session_metadata.json`` file.

    Updates the `session_metadata.json`` in the ``session_dir`` directory
    with the following key/value pairs:

    - end_datetime: NULL.
    - total_episodes: NULL.
    - total_time_steps: NULL.
    """
    with open(session_dir / "session_metadata.json", "r") as file:
        metadata_dict = json.load(file)

    metadata_dict["end_datetime"] = datetime.now().isoformat()
    metadata_dict["total_episodes"] = env.episode_count
    metadata_dict["total_time_steps"] = env.total_step_count

    filepath = session_dir / "session_metadata.json"
    _LOGGER.debug(f"Updating Session Metadata file: {filepath}")
    with open(filepath, "w") as file:
        json.dump(metadata_dict, file)


def _save_agent(agent: OnPolicyAlgorithm, session_path: Path, timestamp_str: str):
    """
    Persist an agent.

    Only works for stable baselines3 agents at present.

    :param session_path: The directory path the session is writing to.
    :param timestamp_str: The session timestamp in the format:
        <yyyy-mm-dd>_<hh-mm-ss>.
    """
    if not isinstance(agent, OnPolicyAlgorithm):
        msg = f"Can only save {OnPolicyAlgorithm} agents, got {type(agent)}."
        _LOGGER.error(msg)
    else:
        filepath = session_path / f"agent_saved_{timestamp_str}"
        agent.save(filepath)
        _LOGGER.debug(f"Trained agent saved as: {filepath}")


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

    return session_path


def run(training_config_path: Union[str, Path], lay_down_config_path: Union[str, Path]):
    """Run the PrimAITE Session.

    :param training_config_path: The training config filepath.
    :param lay_down_config_path: The lay down config filepath.
    """
    # Welcome message
    print("Welcome to the Primary-level AI Training Environment (PrimAITE)")
    uuid = str(uuid4())
    session_timestamp: Final[datetime] = datetime.now()
    session_dir = _get_session_path(session_timestamp)
    timestamp_str = session_timestamp.strftime("%Y-%m-%d_%H-%M-%S")

    print(f"The output directory for this session is: {session_dir}")

    # Create a list of transactions
    # A transaction is an object holding the:
    # - episode #
    # - step #
    # - initial observation space
    # - action
    # - reward
    # - new observation space
    transaction_list = []

    # Create the Primaite environment
    env = Primaite(
        training_config_path=training_config_path,
        lay_down_config_path=lay_down_config_path,
        transaction_list=transaction_list,
        session_path=session_dir,
        timestamp_str=timestamp_str,
    )

    print("Writing Session Metadata file...")

    _write_session_metadata_file(
        session_dir=session_dir, uuid=uuid, session_timestamp=session_timestamp, env=env
    )

    config_values = env.training_config

    # Get the number of steps (which is stored in the child config file)
    config_values.num_steps = env.episode_steps

    # Run environment against an agent
    if config_values.agent_identifier == "GENERIC":
        run_generic(env=env, config_values=config_values)
    elif config_values.agent_identifier == "STABLE_BASELINES3_PPO":
        run_stable_baselines3_ppo(
            env=env,
            config_values=config_values,
            session_path=session_dir,
            timestamp_str=timestamp_str,
        )
    elif config_values.agent_identifier == "STABLE_BASELINES3_A2C":
        run_stable_baselines3_a2c(
            env=env,
            config_values=config_values,
            session_path=session_dir,
            timestamp_str=timestamp_str,
        )

    print("Session finished")
    _LOGGER.debug("Session finished")

    print("Saving transaction logs...")
    write_transaction_to_file(
        transaction_list=transaction_list,
        session_path=session_dir,
        timestamp_str=timestamp_str,
        obs_space_description=env.obs_handler.describe_structure(),
    )

    print("Updating Session Metadata file...")
    _update_session_metadata_file(session_dir=session_dir, env=env)

    print("Finished")
    _LOGGER.debug("Finished")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tc")
    parser.add_argument("--ldc")
    args = parser.parse_args()
    if not args.tc:
        _LOGGER.error(
            "Please provide a training config file using the --tc " "argument"
        )
    if not args.ldc:
        _LOGGER.error(
            "Please provide a lay down config file using the --ldc " "argument"
        )
    run(training_config_path=args.tc, lay_down_config_path=args.ldc)
