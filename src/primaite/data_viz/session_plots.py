# Crown Owned Copyright (C) Dstl 2023. DEFCON 703. Shared in confidence.
from pathlib import Path
from typing import Dict, Optional, Union

import plotly.graph_objects as go
import polars as pl
import yaml
from plotly.graph_objs import Figure

from primaite import _PLATFORM_DIRS


def get_plotly_config() -> Dict:
    """Get the plotly config from primaite_config.yaml."""
    user_config_path = _PLATFORM_DIRS.user_config_path / "primaite_config.yaml"
    with open(user_config_path, "r") as file:
        primaite_config = yaml.safe_load(file)
    return primaite_config["session"]["outputs"]["plots"]


def plot_av_reward_per_episode(
    av_reward_per_episode_csv: Union[str, Path],
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
) -> Figure:
    """
    Plot the average reward per episode from a csv session output.

    :param av_reward_per_episode_csv: The average reward per episode csv
        file path.
    :param title: The plot title. This is optional.
    :param subtitle: The plot subtitle. This is optional.
    :return: The plot as an instance of ``plotly.graph_objs._figure.Figure``.
    """
    df = pl.read_csv(av_reward_per_episode_csv)

    if title:
        if subtitle:
            title = f"{title} <br>{subtitle}</sup>"
    else:
        if subtitle:
            title = subtitle

    config = get_plotly_config()
    layout = go.Layout(
        autosize=config["size"]["auto_size"],
        width=config["size"]["width"],
        height=config["size"]["height"],
    )
    # Create the line graph with a colored line
    fig = go.Figure(layout=layout)
    fig.update_layout(template=config["template"])
    fig.add_trace(
        go.Scatter(
            x=df["Episode"],
            y=df["Average Reward"],
            mode="lines",
            name="Mean Reward per Episode",
        )
    )

    # Set the layout of the graph
    fig.update_layout(
        xaxis={
            "title": "Episode",
            "type": "linear",
            "rangeslider": {"visible": config["range_slider"]},
        },
        yaxis={"title": "Average Reward"},
        title=title,
        showlegend=False,
    )

    return fig
