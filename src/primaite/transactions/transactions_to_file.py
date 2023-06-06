# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""Writes the Transaction log list out to file for evaluation to utilse."""

import csv
import logging
import os.path
from datetime import datetime


def turn_action_space_to_array(_action_space):
    """
    Turns action space into a string array so it can be saved to csv.

    Args:
        _action_space: The action space.
    """
    return_array = []
    for x in range(len(_action_space)):
        return_array.append(str(_action_space[x]))

    return return_array


def turn_obs_space_to_array(_obs_space, _obs_assets, _obs_features):
    """
    Turns observation space into a string array so it can be saved to csv.

    Args:
        _obs_space: The observation space
        _obs_assets: The number of assets (i.e. nodes or links) in the observation space
        _obs_features: The number of features associated with the asset
    """
    return_array = []
    for x in range(_obs_assets):
        for y in range(_obs_features):
            return_array.append(str(_obs_space[x][y]))

    return return_array


def write_transaction_to_file(_transaction_list):
    """
    Writes transaction logs to file to support training evaluation.

    Args:
        _transaction_list: The list of transactions from all steps and all episodes
        _num_episodes: The number of episodes that were conducted.
    """
    # Get the first transaction and use it to determine the makeup of the observation space and action space
    # Label the obs space fields in csv as "OSI_1_1", "OSN_1_1" and action space as "AS_1"
    # This will be tied into the PrimAITE Use Case so that they make sense
    template_transation = _transaction_list[0]
    action_length = template_transation.action_space.size
    obs_shape = template_transation.obs_space_post.shape
    obs_assets = template_transation.obs_space_post.shape[0]
    if len(obs_shape) == 1:
        # bit of a workaround but I think the way transactions are written will change soon
        obs_features = 1
    else:
        obs_features = template_transation.obs_space_post.shape[1]

    # Create the action space headers array
    action_header = []
    for x in range(action_length):
        action_header.append("AS_" + str(x))

    # Create the observation space headers array
    obs_header_initial = []
    obs_header_new = []
    for x in range(obs_assets):
        for y in range(obs_features):
            obs_header_initial.append("OSI_" + str(x) + "_" + str(y))
            obs_header_new.append("OSN_" + str(x) + "_" + str(y))

    # Open up a csv file
    header = ["Timestamp", "Episode", "Step", "Reward"]
    header = header + action_header + obs_header_initial + obs_header_new
    now = datetime.now()  # current date and time
    time = now.strftime("%Y%m%d_%H%M%S")

    try:
        path = "outputs/results/"
        is_dir = os.path.isdir(path)
        if not is_dir:
            os.makedirs(path)

        filename = "outputs/results/all_transactions_" + time + ".csv"
        csv_file = open(filename, "w", encoding="UTF8", newline="")
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(header)

        for transaction in _transaction_list:
            csv_data = [
                str(transaction.timestamp),
                str(transaction.episode_number),
                str(transaction.step_number),
                str(transaction.reward),
            ]
            csv_data = (
                csv_data
                + turn_action_space_to_array(transaction.action_space)
                + turn_obs_space_to_array(
                    transaction.obs_space_pre, obs_assets, obs_features
                )
                + turn_obs_space_to_array(
                    transaction.obs_space_post, obs_assets, obs_features
                )
            )
            csv_writer.writerow(csv_data)

        csv_file.close()
    except Exception:
        logging.error("Could not save the transaction file")
        logging.error("Exception occured", exc_info=True)
