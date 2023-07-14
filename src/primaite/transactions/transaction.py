# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""The Transaction class."""
from datetime import datetime
from typing import List, Optional, Tuple, TYPE_CHECKING, Union

from primaite.common.enums import AgentIdentifier

if TYPE_CHECKING:
    import numpy as np
    from gym import spaces


class Transaction(object):
    """Transaction class."""

    def __init__(self, agent_identifier: AgentIdentifier, episode_number: int, step_number: int) -> None:
        """
        Transaction constructor.

        :param agent_identifier: An identifier for the agent in use
        :param episode_number: The episode number
        :param step_number: The step number
        """
        self.timestamp: datetime = datetime.now()
        "The datetime of the transaction"
        self.agent_identifier: AgentIdentifier = agent_identifier
        "The agent identifier"
        self.episode_number: int = episode_number
        "The episode number"
        self.step_number: int = step_number
        "The step number"
        self.obs_space: "spaces.Space" = None
        "The observation space (pre)"
        self.obs_space_pre: Optional[Union["np.ndarray", Tuple["np.ndarray"]]] = None
        "The observation space before any actions are taken"
        self.obs_space_post: Optional[Union["np.ndarray", Tuple["np.ndarray"]]] = None
        "The observation space after any actions are taken"
        self.reward: Optional[float] = None
        "The reward value"
        self.action_space: Optional[int] = None
        "The action space invoked by the agent"
        self.obs_space_description: Optional[List[str]] = None
        "The env observation space description"

    def as_csv_data(self) -> Tuple[List, List]:
        """
        Converts the Transaction to a csv data row and provides a header.

        :return: A tuple consisting of (header, data).
        """
        if isinstance(self.action_space, int):
            action_length = self.action_space
        else:
            action_length = self.action_space.size

        # Create the action space headers array
        action_header = []
        for x in range(action_length):
            action_header.append("AS_" + str(x))

        # Open up a csv file
        header = ["Timestamp", "Episode", "Step", "Reward"]
        header = header + action_header + self.obs_space_description

        row = [
            str(self.timestamp),
            str(self.episode_number),
            str(self.step_number),
            str(self.reward),
        ]
        row = row + _turn_action_space_to_array(self.action_space) + self.obs_space.tolist()
        return header, row


def _turn_action_space_to_array(action_space: Union[int, List[int]]) -> List[str]:
    """
    Turns action space into a string array so it can be saved to csv.

    :param action_space: The action space
    :return: The action space as an array of strings
    """
    if isinstance(action_space, list):
        return [str(i) for i in action_space]
    else:
        return [str(action_space)]


def _turn_obs_space_to_array(obs_space: "np.ndarray", obs_assets: int, obs_features: int) -> List[str]:
    """
    Turns observation space into a string array so it can be saved to csv.

    :param obs_space: The observation space
    :param obs_assets: The number of assets (i.e. nodes or links) in the observation space
    :param obs_features: The number of features associated with the asset
    :return: The observation space as an array of strings
    """
    return_array = []
    for x in range(obs_assets):
        for y in range(obs_features):
            return_array.append(str(obs_space[x][y]))

    return return_array
