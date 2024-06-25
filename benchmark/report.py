# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import plotly.graph_objects as go
import polars as pl
import yaml
from plotly.graph_objs import Figure
from utils import _get_system_info

import primaite

PLOT_CONFIG = {
    "size": {"auto_size": False, "width": 1500, "height": 900},
    "template": "plotly_white",
    "range_slider": False,
}


def _build_benchmark_results_dict(start_datetime: datetime, metadata_dict: Dict, config: Dict) -> dict:
    num_sessions = len(metadata_dict)  # number of sessions

    averaged_data = {
        "start_timestamp": start_datetime.isoformat(),
        "end_datetime": datetime.now().isoformat(),
        "primaite_version": primaite.__version__,
        "system_info": _get_system_info(),
        "total_sessions": num_sessions,
        "total_episodes": sum(d["total_episodes"] for d in metadata_dict.values()),
        "total_time_steps": sum(d["total_time_steps"] for d in metadata_dict.values()),
        "av_s_per_session": sum(d["total_s"] for d in metadata_dict.values()) / num_sessions,
        "av_s_per_step": sum(d["s_per_step"] for d in metadata_dict.values()) / num_sessions,
        "av_s_per_100_steps_10_nodes": sum(d["s_per_100_steps_10_nodes"] for d in metadata_dict.values())
        / num_sessions,
        "combined_av_reward_per_episode": {},
        "session_av_reward_per_episode": {k: v["av_reward_per_episode"] for k, v in metadata_dict.items()},
        "config": config,
    }

    # find the average of each episode across all sessions
    episodes = metadata_dict[1]["av_reward_per_episode"].keys()

    for episode in episodes:
        combined_av_reward = (
            sum(metadata_dict[k]["av_reward_per_episode"][episode] for k in metadata_dict.keys()) / num_sessions
        )
        averaged_data["combined_av_reward_per_episode"][episode] = combined_av_reward

    return averaged_data


def _get_df_from_episode_av_reward_dict(data: Dict) -> pl.DataFrame:
    data: Dict = {"episode": data.keys(), "av_reward": data.values()}

    return (
        pl.from_dict(data)
        .with_columns(rolling_mean=pl.col("av_reward").rolling_mean(window_size=25))
        .rename({"rolling_mean": "rolling_av_reward"})
    )


def _plot_benchmark_metadata(
    benchmark_metadata_dict: Dict,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
) -> Figure:
    if title:
        if subtitle:
            title = f"{title} <br>{subtitle}</sup>"
    else:
        if subtitle:
            title = subtitle

    layout = go.Layout(
        autosize=PLOT_CONFIG["size"]["auto_size"],
        width=PLOT_CONFIG["size"]["width"],
        height=PLOT_CONFIG["size"]["height"],
    )
    # Create the line graph with a colored line
    fig = go.Figure(layout=layout)
    fig.update_layout(template=PLOT_CONFIG["template"])

    for session, av_reward_dict in benchmark_metadata_dict["session_av_reward_per_episode"].items():
        df = _get_df_from_episode_av_reward_dict(av_reward_dict)
        fig.add_trace(
            go.Scatter(
                x=df["episode"],
                y=df["av_reward"],
                mode="lines",
                name=f"Session {session}",
                opacity=0.25,
                line={"color": "#a6a6a6"},
            )
        )

    df = _get_df_from_episode_av_reward_dict(benchmark_metadata_dict["combined_av_reward_per_episode"])
    fig.add_trace(
        go.Scatter(
            x=df["episode"], y=df["av_reward"], mode="lines", name="Combined Session Av", line={"color": "#FF0000"}
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["episode"],
            y=df["rolling_av_reward"],
            mode="lines",
            name="Rolling Av (Combined Session Av)",
            line={"color": "#4CBB17"},
        )
    )

    # Set the layout of the graph
    fig.update_layout(
        xaxis={
            "title": "Episode",
            "type": "linear",
        },
        yaxis={"title": "Total Reward"},
        title=title,
    )

    return fig


def _plot_all_benchmarks_combined_session_av(results_directory: Path) -> Figure:
    """
    Plot the Benchmark results for each released version of PrimAITE.

    Does this by iterating over the ``benchmark/results`` directory and
    extracting the benchmark metadata json for each version that has been
    benchmarked. The combined_av_reward_per_episode is extracted from each,
    converted into a polars dataframe, and plotted as a scatter line in plotly.
    """
    major_v = primaite.__version__.split(".")[0]
    title = f"Learning Benchmarking of All Released Versions under Major v{major_v}.#.#"
    subtitle = "Rolling Av (Combined Session Av)"
    if title:
        if subtitle:
            title = f"{title} <br>{subtitle}</sup>"
    else:
        if subtitle:
            title = subtitle
    layout = go.Layout(
        autosize=PLOT_CONFIG["size"]["auto_size"],
        width=PLOT_CONFIG["size"]["width"],
        height=PLOT_CONFIG["size"]["height"],
    )
    # Create the line graph with a colored line
    fig = go.Figure(layout=layout)
    fig.update_layout(template=PLOT_CONFIG["template"])

    for dir in results_directory.iterdir():
        if dir.is_dir():
            metadata_file = dir / f"{dir.name}_benchmark_metadata.json"
            with open(metadata_file, "r") as file:
                metadata_dict = json.load(file)
            df = _get_df_from_episode_av_reward_dict(metadata_dict["combined_av_reward_per_episode"])

            fig.add_trace(go.Scatter(x=df["episode"], y=df["rolling_av_reward"], mode="lines", name=dir.name))

    # Set the layout of the graph
    fig.update_layout(
        xaxis={
            "title": "Episode",
            "type": "linear",
        },
        yaxis={"title": "Total Reward"},
        title=title,
    )
    fig["data"][0]["showlegend"] = True

    return fig


def build_benchmark_latex_report(
    benchmark_start_time: datetime, session_metadata: Dict, config_path: Path, results_root_path: Path
) -> None:
    """Generates a latex report of the benchmark run."""
    # generate report folder
    v_str = f"v{primaite.__version__}"

    version_result_dir = results_root_path / v_str
    version_result_dir.mkdir(exist_ok=True, parents=True)

    # load the config file as dict
    with open(config_path, "r") as f:
        cfg_data = yaml.safe_load(f)

    # generate the benchmark metadata dict
    benchmark_metadata_dict = _build_benchmark_results_dict(
        start_datetime=benchmark_start_time, metadata_dict=session_metadata, config=cfg_data
    )
    major_v = primaite.__version__.split(".")[0]
    with open(version_result_dir / f"{v_str}_benchmark_metadata.json", "w") as file:
        json.dump(benchmark_metadata_dict, file, indent=4)
    title = f"PrimAITE v{primaite.__version__.strip()} Learning Benchmark"
    fig = _plot_benchmark_metadata(benchmark_metadata_dict, title=title)
    this_version_plot_path = version_result_dir / f"{title}.png"
    fig.write_image(this_version_plot_path)

    fig = _plot_all_benchmarks_combined_session_av(results_directory=results_root_path)

    all_version_plot_path = version_result_dir / "PrimAITE Versions Learning Benchmark.png"
    fig.write_image(all_version_plot_path)

    data = benchmark_metadata_dict
    primaite_version = data["primaite_version"]

    with open(version_result_dir / f"PrimAITE v{primaite_version} Learning Benchmark.md", "w") as file:
        # Title
        file.write(f"# PrimAITE v{primaite_version} Learning Benchmark\n")
        file.write("## PrimAITE Dev Team\n")
        file.write(f"### {datetime.now().date()}\n")
        file.write("\n---\n")

        sessions = data["total_sessions"]
        episodes = session_metadata[1]["total_episodes"] - 1
        steps = data["config"]["game"]["max_episode_length"]

        # Body
        file.write("## 1 Introduction\n")
        file.write(
            f"PrimAITE v{primaite_version} was benchmarked automatically upon release. Learning rate metrics "
            f"were captured to be referenced during system-level testing and user acceptance testing (UAT).\n"
        )
        file.write(
            f"The benchmarking process consists of running {sessions} training session using the same "
            f"config file. Each session trains an agent for {episodes} episodes, "
            f"with each episode consisting of {steps} steps.\n"
        )
        file.write(
            f"The total reward per episode from each session is captured. This is then used to calculate an "
            f"caverage total reward per episode from the {sessions} individual sessions for smoothing. "
            f"Finally, a 25-widow rolling average of the average total reward per session is calculated for "
            f"further smoothing.\n"
        )

        file.write("## 2 System Information\n")
        i = 1
        file.write(f"### 2.{i} Python\n")
        file.write(f"**Version:** {sys.version}\n")

        for section, section_data in data["system_info"].items():
            i += 1
            if section_data:
                file.write(f"### 2.{i} {section}\n")
                if isinstance(section_data, dict):
                    for key, value in section_data.items():
                        file.write(f"- **{key}:** {value}\n")

        headers_map = {
            "total_sessions": "Total Sessions",
            "total_episodes": "Total Episodes",
            "total_time_steps": "Total Steps",
            "av_s_per_session": "Av Session Duration (s)",
            "av_s_per_step": "Av Step Duration (s)",
            "av_s_per_100_steps_10_nodes": "Av Duration per 100 Steps per 10 Nodes (s)",
        }

        file.write("## 3 Stats\n")
        for section, header in headers_map.items():
            if section.startswith("av_"):
                file.write(f"- **{header}:** {data[section]:.4f}\n")
            else:
                file.write(f"- **{header}:** {data[section]}\n")

        file.write("## 4 Graphs\n")

        file.write(f"### 4.1 v{primaite_version} Learning Benchmark Plot\n")
        file.write(f"![PrimAITE {primaite_version} Learning Benchmark Plot]({this_version_plot_path.name})\n")

        file.write(f"### 4.2 Learning Benchmarking of All Released Versions under Major v{major_v}.#.#\n")
        file.write(
            f"![Learning Benchmarking of All Released Versions under "
            f"Major v{major_v}.#.#]({all_version_plot_path.name})\n"
        )
