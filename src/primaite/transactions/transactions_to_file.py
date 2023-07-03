# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""Writes the Transaction log list out to file for evaluation to utilse."""

import csv
from pathlib import Path

from primaite import getLogger

_LOGGER = getLogger(__name__)


def turn_action_space_to_array(_action_space):
    """
    Turns action space into a string array so it can be saved to csv.

    Args:
        _action_space: The action space.
    """
    if isinstance(_action_space, list):
        return [str(i) for i in _action_space]
    else:
        return [str(_action_space)]


def write_transaction_to_file(
    transaction_list,
    session_path: Path,
    timestamp_str: str,
    obs_space_description: list,
):
    """
    Writes transaction logs to file to support training evaluation.

    :param transaction_list: The list of transactions from all steps and all
        episodes.
    :param session_path: The directory path the session is writing to.
    :param timestamp_str: The session timestamp in the format:
        <yyyy-mm-dd>_<hh-mm-ss>.
    """
    # Get the first transaction and use it to determine the makeup of the
    # observation space and action space
    # Label the obs space fields in csv as "OSI_1_1", "OSN_1_1" and action
    # space as "AS_1"
    # This will be tied into the PrimAITE Use Case so that they make sense
    template_transation = transaction_list[0]
    action_length = template_transation.action_space.size
    # obs_shape = template_transation.obs_space_post.shape
    # obs_assets = template_transation.obs_space_post.shape[0]
    # if len(obs_shape) == 1:
    # bit of a workaround but I think the way transactions are written will change soon
    # obs_features = 1
    # else:
    # obs_features = template_transation.obs_space_post.shape[1]

    # Create the action space headers array
    action_header = []
    for x in range(action_length):
        action_header.append("AS_" + str(x))

    # Create the observation space headers array
    # obs_header_initial = [f"pre_{o}" for o in obs_space_description]
    # obs_header_new = [f"post_{o}" for o in obs_space_description]

    # Open up a csv file
    header = ["Timestamp", "Episode", "Step", "Reward"]
    header = header + action_header + obs_space_description

    try:
        filename = session_path / f"all_transactions_{timestamp_str}.csv"
        _LOGGER.debug(f"Saving transaction logs: {filename}")
        csv_file = open(filename, "w", encoding="UTF8", newline="")
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(header)

        for transaction in transaction_list:
            csv_data = [
                str(transaction.timestamp),
                str(transaction.episode_number),
                str(transaction.step_number),
                str(transaction.reward),
            ]
            csv_data = (
                csv_data
                + turn_action_space_to_array(transaction.action_space)
                + transaction.obs_space.tolist()
            )
            csv_writer.writerow(csv_data)

        csv_file.close()
    except Exception:
        _LOGGER.error("Could not save the transaction file", exc_info=True)
