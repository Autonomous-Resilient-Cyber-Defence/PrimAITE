# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""The Transaction class."""
from datetime import datetime
from typing import List, Tuple


class Transaction(object):
    """Transaction class."""

    def __init__(self, agent_identifier, episode_number, step_number):
        """
        Transaction constructor.

        :param agent_identifier: An identifier for the agent in use
        :param episode_number: The episode number
        :param step_number: The step number
        """
        self.timestamp = datetime.now()
        "The datetime of the transaction"
        self.agent_identifier = agent_identifier
        self.episode_number = episode_number
        "The episode number"
        self.step_number = step_number
        "The step number"
        self.obs_space_pre = None
        "The observation space before any actions are taken"
        self.obs_space_post = None
        "The observation space after any actions are taken"
        self.reward = None
        "The reward value"
        self.action_space = None
        "The action space invoked by the agent"

    def as_csv_data(self) -> Tuple[List, List]:
        """
        Converts the Transaction to a csv data row and provides a header.

        :return: A tuple consisting of (header, data).
        """
        if isinstance(self.action_space, int):
            action_length = self.action_space
        else:
            action_length = self.action_space.size
        obs_shape = self.obs_space_post.shape
        obs_assets = self.obs_space_post.shape[0]
        if len(obs_shape) == 1:
            # A bit of a workaround but I think the way transactions are
            # written will change soon
            obs_features = 1
        else:
            obs_features = self.obs_space_post.shape[1]

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

        row = [
            str(self.timestamp),
            str(self.episode_number),
            str(self.step_number),
            str(self.reward),
        ]
        row = (
            row
            + _turn_action_space_to_array(self.action_space)
            + _turn_obs_space_to_array(
                self.obs_space_pre, obs_assets, obs_features
            )
            + _turn_obs_space_to_array(
                self.obs_space_post, obs_assets, obs_features
            )
        )
        return header, row


def _turn_action_space_to_array(action_space) -> List[str]:
    """
    Turns action space into a string array so it can be saved to csv.

    :param action_space: The action space
    :return: The action space as an array of strings
    """
    if isinstance(action_space, list):
        return [str(i) for i in action_space]
    else:
        return [str(action_space)]


def _turn_obs_space_to_array(obs_space, obs_assets, obs_features) -> List[str]:
    """
    Turns observation space into a string array so it can be saved to csv.

    :param obs_space: The observation space
    :param obs_assets: The number of assets (i.e. nodes or links) in the
        observation space
    :param obs_features: The number of features associated with the asset
    :return: The observation space as an array of strings
    """
    return_array = []
    for x in range(obs_assets):
        for y in range(obs_features):
            return_array.append(str(obs_space[x][y]))

    return return_array
