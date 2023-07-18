import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Final, Tuple
from unittest.mock import patch

import primaite
from primaite.config.lay_down_config import data_manipulation_config_path
from tests.conftest import TempPrimaiteSession

_LOGGER = primaite.getLogger(__name__)

_RESULTS_ROOT: Final[Path] = Path(__file__).parent / "results"
_RESULTS_ROOT.mkdir(exist_ok=True, parents=True)

_OUTPUT_ROOT: Final[Path] = Path(__file__).parent / "output"
# Clear and recreate the output directory
shutil.rmtree(_OUTPUT_ROOT)
_OUTPUT_ROOT.mkdir()


class BenchmarkPrimaiteSession(TempPrimaiteSession):
    """A benchmarking primaite session."""

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
        path = Path(__file__).parent / "config/benchmark_training_config.yaml"
        return BenchmarkPrimaiteSession(path, data_manipulation_config_path())


def _summarise_metadata_dict_results(data: Dict) -> Dict:
    n = len(data)
    averaged_data = {
        "total_sessions": n,
        "total_episodes": sum(d["total_episodes"] for d in data.values()),
        "total_time_steps": sum(d["total_time_steps"] for d in data.values()),
        "av_s_per_session": sum(d["total_s"] for d in data.values()) / n,
        "av_s_per_step": sum(d["s_per_step"] for d in data.values()) / n,
        "av_s_per_100_steps_10_nodes": sum(d["s_per_100_steps_10_nodes"] for d in data.values()) / n,
        "av_reward_per_episode": {},
    }

    av_reward_per_episode_keys = data[1]["av_reward_per_episode"].keys()

    for episode_key in av_reward_per_episode_keys:
        averaged_data["av_reward_per_episode"][episode_key] = (
            sum(data[k]["av_reward_per_episode"][episode_key] for k in data.keys()) / n
        )

    return averaged_data


def run():
    """Run the PrimAITE benchmark."""
    av_reward_per_episode_dicts = {}
    for i in range(1, 11):
        print(f"starting Benchmark Session: {i}")
        with _get_benchmark_primaite_session() as session:
            session.learn()
            av_reward_per_episode_dicts[i] = session.learn_metadata_dict()

    benchmark_metadata = _summarise_metadata_dict_results(av_reward_per_episode_dicts)
    v_str = f"v{primaite.__version__}".strip()

    version_result_dir = _RESULTS_ROOT / v_str
    if version_result_dir.exists():
        shutil.rmtree(version_result_dir)
    version_result_dir.mkdir(exist_ok=True, parents=True)

    with open(version_result_dir / f"{v_str}_benchmark_metadata.json", "w") as file:
        json.dump(benchmark_metadata, file, indent=4)


if __name__ == "__main__":
    run()
