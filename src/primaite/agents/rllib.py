import glob
import time
from enum import Enum
from pathlib import Path
from typing import Union, Optional

from ray.rllib.algorithms import Algorithm
from ray.rllib.algorithms.ppo import PPOConfig
from ray.tune.registry import register_env

from primaite.config import training_config
from primaite.environment.primaite_env import Primaite


class DLFramework(Enum):
    """The DL Frameworks enumeration."""
    TF = "tf"
    TF2 = "tf2"
    TORCH = "torch"


def env_creator(env_config):
    training_config_path = env_config["training_config_path"]
    lay_down_config_path = env_config["lay_down_config_path"]
    return Primaite(training_config_path, lay_down_config_path, [])


def get_ppo_config(
        training_config_path: Union[str, Path],
        lay_down_config_path: Union[str, Path],
        framework: Optional[DLFramework] = DLFramework.TORCH
) -> PPOConfig():
    # Register environment
    register_env("primaite", env_creator)

    # Setup PPO
    config = PPOConfig()

    config_values = training_config.load(training_config_path)

    # Setup our config object to use our environment
    config.environment(
        env="primaite",
        env_config=dict(
            training_config_path=training_config_path,
            lay_down_config_path=lay_down_config_path
        )
    )

    env_config = config_values
    action_type = env_config.action_type
    red_agent = env_config.red_agent_identifier

    if red_agent == "RANDOM" and action_type == "NODE":
        config.training(
            train_batch_size=6000, lr=5e-5
        )  # number of steps in a training iteration
    elif red_agent == "RANDOM" and action_type != "NODE":
        config.training(train_batch_size=6000, lr=5e-5)
    elif red_agent == "CONFIG" and action_type == "NODE":
        config.training(train_batch_size=400, lr=5e-5)
    elif red_agent == "CONFIG" and action_type != "NONE":
        config.training(train_batch_size=500, lr=5e-5)
    else:
        config.training(train_batch_size=500, lr=5e-5)

    # Decide if you want torch or tensorflow DL framework. Default is "tf"
    config.framework(framework=framework.value)

    # Set the log level to DEBUG, INFO, WARN, or ERROR
    config.debugging(seed=415, log_level="ERROR")

    # Setup evaluation
    # Explicitly set "explore"=False to override default
    # config.evaluation(
    #    evaluation_interval=100,
    #    evaluation_duration=20,
    #    # evaluation_duration_unit="timesteps",) #default episodes
    #    evaluation_config={"explore": False},
    # )

    # Setup sampling rollout workers
    config.rollouts(
        num_rollout_workers=4,
        num_envs_per_worker=1,
        horizon=128,  # num parralel workiers
    )  # max num steps in an episode

    config.build()  # Build config

    return config


def train(
        num_iterations: int,
        config: Optional[PPOConfig] = None,
        algo: Optional[Algorithm] = None
):
    """

    Requires either the algorithm config (new model) or the algorithm itself (continue training from checkpoint)
    """

    start_time = time.time()

    if algo is None:
        algo = config.build()
    elif config is None:
        config = algo.get_config()

    print(f"Algorithm type: {type(algo)}")

    # iterations are not the same as episodes.
    for i in range(num_iterations):
        result = algo.train()
        # # Save every 10 iterations or after last iteration in training
        # if (i % 100 == 0) or (i == num_iterations - 1):
        print(
            f"Iteration={i}, Mean Reward={result['episode_reward_mean']:.2f}")
        # save checkpoint file
        checkpoint_file = algo.save("./")
        print(f"Checkpoint saved at {checkpoint_file}")

    # convert num_iterations to num_episodes
    num_episodes = len(
        result["hist_stats"]["episode_lengths"]) * num_iterations
    # convert num_iterations to num_timesteps
    num_timesteps = sum(
        result["hist_stats"]["episode_lengths"] * num_iterations)
    # calculate number of wins

    # train time
    print(f"Training took {time.time() - start_time:.2f} seconds")
    print(
        f"Number of episodes {num_episodes}, Number of timesteps: {num_timesteps}")
    return result


def load_model_from_checkpoint(config, checkpoint=None):
    # create an empty Algorithm
    algo = config.build()

    if checkpoint is None:
        # Get the checkpoint with the highest iteration number
        checkpoint = get_most_recent_checkpoint(config)

    # restore the agent from the checkpoint
    algo.restore(checkpoint)

    return algo


def get_most_recent_checkpoint(config):
    """
    Get the most recent checkpoint for specified action type, red agent and algorithm
    """

    env_config = list(config.env_config.values())[0]
    action_type = env_config.action_type
    red_agent = env_config.red_agent_identifier
    algo_name = config.algo_class.__name__

    # Gets the latest checkpoint (highest iteration not datetime) to use as the final trained model
    relevant_checkpoints = glob.glob(
        f"/app/outputs/agents/{action_type}/{red_agent}/{algo_name}/*"
    )
    checkpoint_numbers = [int(i.split("_")[1]) for i in relevant_checkpoints]
    max_checkpoint = str(max(checkpoint_numbers))
    checkpoint_number_to_use = "0" * (6 - len(max_checkpoint)) + max_checkpoint
    checkpoint = (
            relevant_checkpoints[0].split("_")[0]
            + "_"
            + checkpoint_number_to_use
            + "/rllib_checkpoint.json"
    )

    return checkpoint
