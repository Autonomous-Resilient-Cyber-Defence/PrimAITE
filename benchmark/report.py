# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import plotly.graph_objects as go
import polars as pl
import yaml
from plotly.graph_objs import Figure
from pylatex import Command, Document
from pylatex import Figure as LatexFigure
from pylatex import Section, Subsection, Tabular
from pylatex.utils import bold
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
        yaxis={"title": "Average Reward"},
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
    title = "PrimAITE Versions Learning Benchmark"
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
        yaxis={"title": "Average Reward"},
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
    if version_result_dir.exists():
        shutil.rmtree(version_result_dir)
    version_result_dir.mkdir(exist_ok=True, parents=True)

    # load the config file as dict
    with open(config_path, "r") as f:
        cfg_data = yaml.safe_load(f)

    # generate the benchmark metadata dict
    benchmark_metadata_dict = _build_benchmark_results_dict(
        start_datetime=benchmark_start_time, metadata_dict=session_metadata, config=cfg_data
    )

    with open(version_result_dir / f"{v_str}_benchmark_metadata.json", "w") as file:
        json.dump(benchmark_metadata_dict, file, indent=4)
    title = f"PrimAITE v{primaite.__version__.strip()} Learning Benchmark"
    fig = _plot_benchmark_metadata(benchmark_metadata_dict, title=title)
    this_version_plot_path = version_result_dir / f"{title}.png"
    fig.write_image(this_version_plot_path)

    fig = _plot_all_benchmarks_combined_session_av(results_directory=results_root_path)

    all_version_plot_path = results_root_path / "PrimAITE Versions Learning Benchmark.png"
    fig.write_image(all_version_plot_path)

    geometry_options = {"tmargin": "2.5cm", "rmargin": "2.5cm", "bmargin": "2.5cm", "lmargin": "2.5cm"}
    data = benchmark_metadata_dict
    primaite_version = data["primaite_version"]

    # Create a new document
    doc = Document("report", geometry_options=geometry_options)
    # Title
    doc.preamble.append(Command("title", f"PrimAITE {primaite_version} Learning Benchmark"))
    doc.preamble.append(Command("author", "PrimAITE Dev Team"))
    doc.preamble.append(Command("date", datetime.now().date()))
    doc.append(Command("maketitle"))

    sessions = data["total_sessions"]
    episodes = session_metadata[1]["total_episodes"] - 1
    steps = data["config"]["game"]["max_episode_length"]

    # Body
    with doc.create(Section("Introduction")):
        doc.append(
            f"PrimAITE v{primaite_version} was benchmarked automatically upon release. Learning rate metrics "
            f"were captured to be referenced during system-level testing and user acceptance testing (UAT)."
        )
        doc.append(
            f"\nThe benchmarking process consists of running {sessions} training session using the same "
            f"config file. Each session trains an agent for {episodes} episodes, "
            f"with each episode consisting of {steps} steps."
        )
        doc.append(
            f"\nThe mean reward per episode from each session is captured. This is then used to calculate a "
            f"combined average reward per episode from the {sessions} individual sessions for smoothing. "
            f"Finally, a 25-widow rolling average of the combined average reward per session is calculated for "
            f"further smoothing."
        )

    with doc.create(Section("System Information")):
        with doc.create(Subsection("Python")):
            with doc.create(Tabular("|l|l|")) as table:
                table.add_hline()
                table.add_row((bold("Version"), sys.version))
                table.add_hline()
        for section, section_data in data["system_info"].items():
            if section_data:
                with doc.create(Subsection(section)):
                    if isinstance(section_data, dict):
                        with doc.create(Tabular("|l|l|")) as table:
                            table.add_hline()
                            for key, value in section_data.items():
                                table.add_row((bold(key), value))
                                table.add_hline()
                    elif isinstance(section_data, list):
                        headers = section_data[0].keys()
                        tabs_str = "|".join(["l" for _ in range(len(headers))])
                        tabs_str = f"|{tabs_str}|"
                        with doc.create(Tabular(tabs_str)) as table:
                            table.add_hline()
                            table.add_row([bold(h) for h in headers])
                            table.add_hline()
                            for item in section_data:
                                table.add_row(item.values())
                                table.add_hline()

    headers_map = {
        "total_sessions": "Total Sessions",
        "total_episodes": "Total Episodes",
        "total_time_steps": "Total Steps",
        "av_s_per_session": "Av Session Duration (s)",
        "av_s_per_step": "Av Step Duration (s)",
        "av_s_per_100_steps_10_nodes": "Av Duration per 100 Steps per 10 Nodes (s)",
    }
    with doc.create(Section("Stats")):
        with doc.create(Subsection("Benchmark Results")):
            with doc.create(Tabular("|l|l|")) as table:
                table.add_hline()
                for section, header in headers_map.items():
                    if section.startswith("av_"):
                        table.add_row((bold(header), f"{data[section]:.4f}"))
                    else:
                        table.add_row((bold(header), data[section]))
                    table.add_hline()

    with doc.create(Section("Graphs")):
        with doc.create(Subsection(f"PrimAITE {primaite_version} Learning Benchmark Plot")):
            with doc.create(LatexFigure(position="h!")) as pic:
                pic.add_image(str(this_version_plot_path))
                pic.add_caption(f"PrimAITE {primaite_version} Learning Benchmark Plot")

        with doc.create(Subsection("PrimAITE All Versions Learning Benchmark Plot")):
            with doc.create(LatexFigure(position="h!")) as pic:
                pic.add_image(str(all_version_plot_path))
                pic.add_caption("PrimAITE All Versions Learning Benchmark Plot")

    doc.generate_pdf(str(this_version_plot_path).replace(".png", ""), clean_tex=True)
