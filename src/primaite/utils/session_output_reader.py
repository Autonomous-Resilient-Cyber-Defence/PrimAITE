from pathlib import Path
from typing import Dict, Union

# Using polars as it's faster than Pandas; it will speed things up when
# files get big!
import polars as pl


def av_rewards_dict(av_rewards_csv_file: Union[str, Path]) -> Dict[int, float]:
    """Read an average rewards per episode csv file and return as a dict.

    The dictionary keys are the episode number, and the values are the mean reward that episode.

    :param av_rewards_csv_file: The average rewards per episode csv file path.
    :return: The average rewards per episode cdv as a dict.
    """
    d = pl.read_csv(av_rewards_csv_file).to_dict()
    return {v: d["Average Reward"][i] for i, v in enumerate(d["Episode"])}
