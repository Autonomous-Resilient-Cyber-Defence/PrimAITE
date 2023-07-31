# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
import json
import platform
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Final, Optional, Tuple, Union
from unittest.mock import patch

import GPUtil
import plotly.graph_objects as go
import polars as pl
import psutil
import yaml
from plotly.graph_objs import Figure
from pylatex import Command, Document
from pylatex import Figure as LatexFigure
from pylatex import Section, Subsection, Tabular
from pylatex.utils import bold

import primaite
from primaite.config.lay_down_config import data_manipulation_config_path
from primaite.data_viz.session_plots import get_plotly_config
from primaite.environment.primaite_env import Primaite
from primaite.primaite_session import PrimaiteSession

_LOGGER = primaite.getLogger(__name__)

_BENCHMARK_ROOT = Path(__file__).parent
_RESULTS_ROOT: Final[Path] = _BENCHMARK_ROOT / "results"
_RESULTS_ROOT.mkdir(exist_ok=True, parents=True)

_OUTPUT_ROOT: Final[Path] = _BENCHMARK_ROOT / "output"
# Clear and recreate the output directory
if _OUTPUT_ROOT.exists():
    shutil.rmtree(_OUTPUT_ROOT)
_OUTPUT_ROOT.mkdir()

_TRAINING_CONFIG_PATH = _BENCHMARK_ROOT / "config" / "benchmark_training_config.yaml"
_LAY_DOWN_CONFIG_PATH = data_manipulation_config_path()


def get_size(size_bytes: int) -> str:
    """
    Scale bytes to its proper format.

    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'

    :
    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if size_bytes < factor:
            return f"{size_bytes:.2f}{unit}B"
        size_bytes /= factor


def _get_system_info() -> Dict:
    """Builds and returns a dict containing system info."""
    uname = platform.uname()
    cpu_freq = psutil.cpu_freq()
    virtual_mem = psutil.virtual_memory()
    swap_mem = psutil.swap_memory()
    gpus = GPUtil.getGPUs()
    return {
        "System": {
            "OS": uname.system,
            "OS Version": uname.version,
            "Machine": uname.machine,
            "Processor": uname.processor,
        },
        "CPU": {
            "Physical Cores": psutil.cpu_count(logical=False),
            "Total Cores": psutil.cpu_count(logical=True),
            "Max Frequency": f"{cpu_freq.max:.2f}Mhz",
        },
        "Memory": {"Total": get_size(virtual_mem.total), "Swap Total": get_size(swap_mem.total)},
        "GPU": [{"Name": gpu.name, "Total Memory": f"{gpu.memoryTotal}MB"} for gpu in gpus],
    }


def _build_benchmark_latex_report(
    benchmark_metadata_dict: Dict, this_version_plot_path: Path, all_version_plot_path: Path
) -> None:
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
    episodes = data["training_config"]["num_train_episodes"]
    steps = data["training_config"]["num_train_steps"]

    # Body
    with doc.create(Section("Introduction")):
        doc.append(
            f"PrimAITE v{primaite_version} was benchmarked automatically upon release. Learning rate metrics "
            f"were captured to be referenced during system-level testing and user acceptance testing (UAT)."
        )
        doc.append(
            f"\nThe benchmarking process consists of running {sessions} training session using the same "
            f"training and lay down config files. Each session trains an agent for {episodes} episodes, "
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


class BenchmarkPrimaiteSession(PrimaiteSession):
    """A benchmarking primaite session."""

    def __init__(
        self,
        training_config_path: Union[str, Path],
        lay_down_config_path: Union[str, Path],
    ) -> None:
        super().__init__(training_config_path, lay_down_config_path)
        self.setup()

    @property
    def env(self) -> Primaite:
        """Direct access to the env for ease of testing."""
        return self._agent_session._env  # noqa

    def __enter__(self) -> "BenchmarkPrimaiteSession":
        return self

    # TODO: typehints uncertain
    def __exit__(self, type: Any, value: Any, tb: Any) -> None:
        shutil.rmtree(self.session_path)
        _LOGGER.debug(f"Deleted benchmark session directory: {self.session_path}")

    def _learn_benchmark_durations(self) -> Tuple[float, float, float]:
        """
        Calculate and return the learning benchmark durations.

        Calculates the:
        - Total learning time in seconds
        - Total learning time per time step in seconds
        - Total learning time per 100 time steps per 10 nodes in seconds

        :return: The learning benchmark durations as a Tuple of three floats:
            Tuple[total_s, s_per_step, s_per_100_steps_10_nodes].
        """
        data = self.metadata_file_as_dict()
        start_dt = datetime.fromisoformat(data["start_datetime"])
        end_dt = datetime.fromisoformat(data["end_datetime"])
        delta = end_dt - start_dt
        total_s = delta.total_seconds()

        total_steps = data["learning"]["total_time_steps"]
        s_per_step = total_s / total_steps

        num_nodes = self.env.num_nodes
        num_intervals = total_steps / 100
        av_interval_time = total_s / num_intervals
        s_per_100_steps_10_nodes = av_interval_time / (num_nodes / 10)

        return total_s, s_per_step, s_per_100_steps_10_nodes

    def learn_metadata_dict(self) -> Dict[str, Any]:
        """Metadata specific to the learning session."""
        total_s, s_per_step, s_per_100_steps_10_nodes = self._learn_benchmark_durations()
        return {
            "total_episodes": self.env.actual_episode_count,
            "total_time_steps": self.env.total_step_count,
            "total_s": total_s,
            "s_per_step": s_per_step,
            "s_per_100_steps_10_nodes": s_per_100_steps_10_nodes,
            "av_reward_per_episode": self.learn_av_reward_per_episode_dict(),
        }


def _get_benchmark_session_path(session_timestamp: datetime) -> Path:
    return _OUTPUT_ROOT / session_timestamp.strftime("%Y-%m-%d_%H-%M-%S")


def _get_benchmark_primaite_session() -> BenchmarkPrimaiteSession:
    with patch("primaite.agents.agent_abc.get_session_path", _get_benchmark_session_path) as mck:
        mck.session_timestamp = datetime.now()
        return BenchmarkPrimaiteSession(_TRAINING_CONFIG_PATH, _LAY_DOWN_CONFIG_PATH)


def _build_benchmark_results_dict(start_datetime: datetime, metadata_dict: Dict) -> dict:
    n = len(metadata_dict)
    with open(_TRAINING_CONFIG_PATH, "r") as file:
        training_config_dict = yaml.safe_load(file)
    with open(_LAY_DOWN_CONFIG_PATH, "r") as file:
        lay_down_config_dict = yaml.safe_load(file)
    averaged_data = {
        "start_timestamp": start_datetime.isoformat(),
        "end_datetime": datetime.now().isoformat(),
        "primaite_version": primaite.__version__,
        "system_info": _get_system_info(),
        "total_sessions": n,
        "total_episodes": sum(d["total_episodes"] for d in metadata_dict.values()),
        "total_time_steps": sum(d["total_time_steps"] for d in metadata_dict.values()),
        "av_s_per_session": sum(d["total_s"] for d in metadata_dict.values()) / n,
        "av_s_per_step": sum(d["s_per_step"] for d in metadata_dict.values()) / n,
        "av_s_per_100_steps_10_nodes": sum(d["s_per_100_steps_10_nodes"] for d in metadata_dict.values()) / n,
        "combined_av_reward_per_episode": {},
        "session_av_reward_per_episode": {k: v["av_reward_per_episode"] for k, v in metadata_dict.items()},
        "training_config": training_config_dict,
        "lay_down_config": lay_down_config_dict,
    }

    episodes = metadata_dict[1]["av_reward_per_episode"].keys()

    for episode in episodes:
        combined_av_reward = sum(metadata_dict[k]["av_reward_per_episode"][episode] for k in metadata_dict.keys()) / n
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

    config = get_plotly_config()
    layout = go.Layout(
        autosize=config["size"]["auto_size"],
        width=config["size"]["width"],
        height=config["size"]["height"],
    )
    # Create the line graph with a colored line
    fig = go.Figure(layout=layout)
    fig.update_layout(template=config["template"])

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


def _plot_all_benchmarks_combined_session_av() -> Figure:
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
    config = get_plotly_config()
    layout = go.Layout(
        autosize=config["size"]["auto_size"],
        width=config["size"]["width"],
        height=config["size"]["height"],
    )
    # Create the line graph with a colored line
    fig = go.Figure(layout=layout)
    fig.update_layout(template=config["template"])

    for dir in _RESULTS_ROOT.iterdir():
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


def run() -> None:
    """Run the PrimAITE benchmark."""
    start_datetime = datetime.now()
    av_reward_per_episode_dicts = {}
    for i in range(1, 11):
        print(f"Starting Benchmark Session: {i}")
        with _get_benchmark_primaite_session() as session:
            session.learn()
            av_reward_per_episode_dicts[i] = session.learn_metadata_dict()

    benchmark_metadata = _build_benchmark_results_dict(
        start_datetime=start_datetime, metadata_dict=av_reward_per_episode_dicts
    )
    v_str = f"v{primaite.__version__}"

    version_result_dir = _RESULTS_ROOT / v_str
    if version_result_dir.exists():
        shutil.rmtree(version_result_dir)
    version_result_dir.mkdir(exist_ok=True, parents=True)

    with open(version_result_dir / f"{v_str}_benchmark_metadata.json", "w") as file:
        json.dump(benchmark_metadata, file, indent=4)
    title = f"PrimAITE v{primaite.__version__.strip()} Learning Benchmark"
    fig = _plot_benchmark_metadata(benchmark_metadata, title=title)
    this_version_plot_path = version_result_dir / f"{title}.png"
    fig.write_image(this_version_plot_path)

    fig = _plot_all_benchmarks_combined_session_av()

    all_version_plot_path = _RESULTS_ROOT / "PrimAITE Versions Learning Benchmark.png"
    fig.write_image(all_version_plot_path)

    _build_benchmark_latex_report(benchmark_metadata, this_version_plot_path, all_version_plot_path)


if __name__ == "__main__":
    run()
