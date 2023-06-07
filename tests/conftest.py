# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
import time
from pathlib import Path
from typing import Union

from primaite.environment.primaite_env import Primaite

ACTION_SPACE_NODE_VALUES = 1
ACTION_SPACE_NODE_ACTION_VALUES = 1


def _get_primaite_env_from_config(
    training_config_path: Union[str, Path], lay_down_config_path: Union[str, Path]
):
    """Takes a config path and returns the created instance of Primaite."""
    env = Primaite(
        training_config_path=training_config_path,
        lay_down_config_path=lay_down_config_path,
        transaction_list=[],
    )
    config_values = env.config_values
    config_values.num_steps = env.episode_steps

    # TOOD: This needs t be refactored to happen outside. Should be part of
    # a main Session class.
    if env.config_values.agent_identifier == "GENERIC":
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
            action = env.action_space.sample()

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
