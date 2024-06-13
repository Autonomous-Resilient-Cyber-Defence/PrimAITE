# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
# flake8: noqa
raise DeprecationWarning(
    "Benchmarking depends on deprecated functionality and it has not been updated to primaite v3 yet."
)
# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from pathlib import Path
from typing import Any, Dict, Tuple, Union

# Using polars as it's faster than Pandas; it will speed things up when
# files get big!
import polars as pl


def total_rewards_dict(total_rewards_csv_file: Union[str, Path]) -> Dict[int, float]:
    """
    Read an average rewards per episode csv file and return as a dict.

    The dictionary keys are the episode number, and the values are the mean reward that episode.

    :param total_rewards_csv_file: The average rewards per episode csv file path.
    :return: The average rewards per episode csv as a dict.
    """
    df_dict = pl.read_csv(total_rewards_csv_file).to_dict()

    return {int(v): df_dict["Average Reward"][i] for i, v in enumerate(df_dict["Episode"])}


def all_transactions_dict(all_transactions_csv_file: Union[str, Path]) -> Dict[Tuple[int, int], Dict[str, Any]]:
    """
    Read an all transactions csv file and return as a dict.

    The dict keys are a tuple with the structure (episode, step). The dict
    values are the remaining columns as a dict.

    :param all_transactions_csv_file: The all transactions csv file path.
    :return: The all transactions csv file as a dict.
    """
    df_dict = pl.read_csv(all_transactions_csv_file).to_dict()
    new_dict = {}

    episodes = df_dict["Episode"]
    steps = df_dict["Step"]
    keys = list(df_dict.keys())

    for i in range(len(episodes)):
        key = (episodes[i], steps[i])
        value_dict = {key: df_dict[key][i] for key in keys if key not in ["Episode", "Step"]}
        new_dict[key] = value_dict

    return new_dict
