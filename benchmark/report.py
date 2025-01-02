# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
import json
import sys
from datetime import datetime
from os import PathLike
from pathlib import Path
from typing import Dict, Optional

import plotly.graph_objects as go
import polars as pl
import yaml
from plotly.graph_objs import Figure
from utils import _get_system_info

import primaite

PLOT_CONFIG = {
    "size": {"auto_size": False, "width": 800, "height": 640},
    "template": "plotly_white",
    "range_slider": False,
}


def _build_benchmark_results_dict(start_datetime: datetime, metadata_dict: Dict, config: Dict) -> dict:
    """
    Constructs a dictionary aggregating benchmark results from multiple sessions.

    :param start_datetime: The datetime when the benchmarking started.
    :param metadata_dict: Dictionary containing metadata for each session.
    :param config: Configuration settings used during the benchmarking.
    :return: A dictionary containing aggregated data and metadata from the benchmarking sessions.
    """
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
        "combined_total_reward_per_episode": {},
        "session_total_reward_per_episode": {k: v["total_reward_per_episode"] for k, v in metadata_dict.items()},
        "config": config,
    }

    # find the average of each episode across all sessions
    episodes = metadata_dict[1]["total_reward_per_episode"].keys()

    for episode in episodes:
        combined_av_reward = (
            sum(metadata_dict[k]["total_reward_per_episode"][episode] for k in metadata_dict.keys()) / num_sessions
        )
        averaged_data["combined_total_reward_per_episode"][episode] = combined_av_reward

    return averaged_data


def _get_df_from_episode_av_reward_dict(data: Dict) -> pl.DataFrame:
    """
    Converts a dictionary of episode average rewards into a Polars DataFrame.

    :param data: Dictionary with episodes as keys and average rewards as values.
    :return: Polars DataFrame with episodes and average rewards, including a rolling average.
    """
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
    """
    Plots benchmark metadata as a line graph using Plotly.

    :param benchmark_metadata_dict: Dictionary containing the total reward per episode and session.
    :param title: Optional title for the graph.
    :param subtitle: Optional subtitle for the graph.
    :return: Plotly figure object representing the benchmark metadata plot.
    """
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

    for session, av_reward_dict in benchmark_metadata_dict["session_total_reward_per_episode"].items():
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

    df = _get_df_from_episode_av_reward_dict(benchmark_metadata_dict["combined_total_reward_per_episode"])
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
    fig.update_layout(
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255,255,255,0.3)",
        )
    )
    for trace in fig["data"]:
        if trace["name"].startswith("Session"):
            trace["showlegend"] = False
    fig["data"][0]["name"] = "Individual Sessions"
    fig["data"][0]["showlegend"] = True

    return fig


def _plot_all_benchmarks_combined_session_av(results_directory: Path) -> Figure:
    """
    Plot the Benchmark results for each released version of PrimAITE.

    Does this by iterating over the ``benchmark/results`` directory and
    extracting the benchmark metadata json for each version that has been
    benchmarked. The combined_total_reward_per_episode is extracted from each,
    converted into a polars dataframe, and plotted as a scatter line in plotly.
    """
    major_v = primaite.__version__.split(".")[0]
    title = f"Learning Benchmark of Minor and Bugfix Releases for Major Version {major_v}"
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
            df = _get_df_from_episode_av_reward_dict(metadata_dict["combined_total_reward_per_episode"])

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
    fig.update_layout(legend=dict(yanchor="top", y=-0.2, xanchor="left", x=0.01, orientation="h"))

    return fig


def _get_performance_benchmark_for_all_version_dict(results_directory: Path) -> Dict[str, float]:
    """
    Gathers performance benchmarks for all versions of the software stored in a specified directory.

    This function iterates through each directory within the specified results directory,
    extracts the av_s_per_100_steps_10_nodes from the benchmark_metadata.json files, and aggregates it into a
    dictionary.

    :param results_directory: The directory containing subdirectories for each version's benchmark data.
    :return: A dictionary with version numbers as keys and their corresponding average performance benchmark
        (average time per 100 steps on 10 nodes) as values.
    """
    performance_benchmark_dict = {}
    for dir in results_directory.iterdir():
        if dir.is_dir():
            metadata_file = dir / f"{dir.name}_benchmark_metadata.json"
            with open(metadata_file, "r") as file:
                metadata_dict = json.load(file)
                version = metadata_dict["primaite_version"]
                performance_benchmark_dict[version] = metadata_dict["av_s_per_100_steps_10_nodes"]
    return performance_benchmark_dict


def _plot_av_s_per_100_steps_10_nodes(
    version_times_dict: Dict[str, float],
) -> Figure:
    """
    Creates a bar chart visualising the performance of each version of PrimAITE.

    Performance is based on the average training time per 100 steps on 10 nodes.

    :param version_times_dict: A dictionary with software versions as keys and average times as values.
    :return: A Plotly figure object representing the bar chart of the performance metrics.
    """
    major_v = primaite.__version__.split(".")[0]
    title = f"Performance of Minor and Bugfix Releases for Major Version {major_v}"
    subtitle = "Average Training Time per 100 Steps on 10 Nodes "
    title = f"{title} <br><sub>{subtitle}</sub>"

    layout = go.Layout(
        autosize=PLOT_CONFIG["size"]["auto_size"],
        width=PLOT_CONFIG["size"]["width"],
        height=PLOT_CONFIG["size"]["height"],
    )
    fig = go.Figure(layout=layout)
    fig.update_layout(template=PLOT_CONFIG["template"])

    versions = sorted(list(version_times_dict.keys()))
    times = [version_times_dict[version] for version in versions]

    fig.add_trace(go.Bar(x=versions, y=times, text=times, textposition="auto", texttemplate="%{y:.3f}"))

    fig.update_layout(
        xaxis_title="PrimAITE Version",
        yaxis_title="Avg Time per 100 Steps on 10 Nodes (seconds)",
        title=title,
    )

    return fig


def build_benchmark_md_report(
    benchmark_start_time: datetime,
    session_metadata: Dict,
    config_path: Path,
    results_root_path: Path,
    output_path: PathLike,
) -> None:
    """
    Generates a Markdown report for a benchmarking session, documenting performance metrics and graphs.

    This function orchestrates the creation of several graphs depicting various performance benchmarks and aggregates
    them into a markdown document that includes comprehensive system and benchmark information.

    :param benchmark_start_time: The datetime object representing when the benchmarking process was initiated.
    :param session_metadata: A dictionary containing metadata for each benchmarking session.
    :param config_path: A pathlib.Path object pointing to the configuration file used for the benchmark sessions.
    :param results_root_path: A pathlib.Path object pointing to the directory where the results and graphs should be
        saved.
    """
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

    filename = f"PrimAITE Learning Benchmark of Minor and Bugfix Releases for Major Version {major_v}.png"

    all_version_plot_path = version_result_dir / filename
    fig.write_image(all_version_plot_path)

    performance_benchmark_dict = _get_performance_benchmark_for_all_version_dict(results_directory=results_root_path)
    fig = _plot_av_s_per_100_steps_10_nodes(performance_benchmark_dict)
    filename = f"PrimAITE Performance of Minor and Bugfix Releases for Major Version {major_v}.png"
    performance_benchmark_plot_path = version_result_dir / filename
    fig.write_image(performance_benchmark_plot_path)

    data = benchmark_metadata_dict
    primaite_version = data["primaite_version"]

    with open(output_path, "w") as file:
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

        file.write(f"### 4.2 Learning Benchmark of Minor and Bugfix Releases for Major Version {major_v}\n")
        file.write(
            f"![Learning Benchmark of Minor and Bugfix Releases for Major Version {major_v}]"
            f"({all_version_plot_path.name})\n"
        )

        file.write(f"### 4.3 Performance of Minor and Bugfix Releases for Major Version {major_v}\n")
        file.write(
            f"![Performance of Minor and Bugfix Releases for Major Version {major_v}]"
            f"({performance_benchmark_plot_path.name})\n"
        )


def md2pdf(md_path: PathLike, pdf_path: PathLike, css_path: PathLike) -> None:
    """Generate PDF version of Markdown report."""
    from md2pdf.core import md2pdf

    md2pdf(
        pdf_file_path=pdf_path,
        md_file_path=md_path,
        base_url=Path(md_path).parent,
        css_file_path=css_path,
    )
