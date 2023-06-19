# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""
The main PrimAITE session runner module.

TODO: This will eventually be refactored out into a proper Session class.
TODO: The passing about of session_path and timestamp_str is temporary and
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
from primaite.primaite_session import PrimaiteSession
from primaite.transactions.transactions_to_file import \
    write_transaction_to_file

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




def run(training_config_path: Union[str, Path], lay_down_config_path: Union[str, Path]):
    """Run the PrimAITE Session.

    :param training_config_path: The training config filepath.
    :param lay_down_config_path: The lay down config filepath.
    """
    session = PrimaiteSession(training_config_path, lay_down_config_path)

    session.setup()
    session.learn()


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


