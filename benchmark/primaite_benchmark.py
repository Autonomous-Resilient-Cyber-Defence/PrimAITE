# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Final, Tuple

from report import build_benchmark_latex_report
from stable_baselines3 import PPO

import primaite
from benchmark import BenchmarkPrimaiteGymEnv
from primaite.config.load import data_manipulation_config_path

_LOGGER = primaite.getLogger(__name__)

_MAJOR_V = primaite.__version__.split(".")[0]

_BENCHMARK_ROOT = Path(__file__).parent
_RESULTS_ROOT: Final[Path] = _BENCHMARK_ROOT / "results" / f"v{_MAJOR_V}"
_VERSION_ROOT: Final[Path] = _RESULTS_ROOT / f"v{primaite.__version__}"
_SESSION_METADATA_ROOT: Final[Path] = _VERSION_ROOT / "session_metadata"

_SESSION_METADATA_ROOT.mkdir(parents=True, exist_ok=True)


class BenchmarkSession:
    """Benchmark Session class."""

    gym_env: BenchmarkPrimaiteGymEnv
    """Gym environment used by the session to train."""

    num_episodes: int
    """Number of episodes to run the training session."""

    episode_len: int
    """The number of steps per episode."""

    total_steps: int
    """Number of steps to run the training session."""

    batch_size: int
    """Number of steps for each episode."""

    learning_rate: float
    """Learning rate for the model."""

    start_time: datetime
    """Start time for the session."""

    end_time: datetime
    """End time for the session."""

    def __init__(
        self,
        gym_env: BenchmarkPrimaiteGymEnv,
        episode_len: int,
        num_episodes: int,
        n_steps: int,
        batch_size: int,
        learning_rate: float,
    ):
        """Initialise the BenchmarkSession."""
        self.gym_env = gym_env
        self.episode_len = episode_len
        self.n_steps = n_steps
        self.num_episodes = num_episodes
        self.total_steps = self.num_episodes * self.episode_len
        self.batch_size = batch_size
        self.learning_rate = learning_rate

    def train(self):
        """Run the training session."""
        # start timer for session
        self.start_time = datetime.now()
        model = PPO(
            policy="MlpPolicy",
            env=self.gym_env,
            learning_rate=self.learning_rate,
            n_steps=self.n_steps,
            batch_size=self.batch_size,
            verbose=0,
            tensorboard_log="./PPO_UC2/",
        )
        model.learn(total_timesteps=self.total_steps)

        # end timer for session
        self.end_time = datetime.now()

        self.session_metadata = self.generate_learn_metadata_dict()

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
        delta = self.end_time - self.start_time
        total_s = delta.total_seconds()

        total_steps = self.batch_size * self.num_episodes
        s_per_step = total_s / total_steps

        num_nodes = len(self.gym_env.game.simulation.network.nodes)
        num_intervals = total_steps / 100
        av_interval_time = total_s / num_intervals
        s_per_100_steps_10_nodes = av_interval_time / (num_nodes / 10)

        return total_s, s_per_step, s_per_100_steps_10_nodes

    def generate_learn_metadata_dict(self) -> Dict[str, Any]:
        """Metadata specific to the learning session."""
        total_s, s_per_step, s_per_100_steps_10_nodes = self._learn_benchmark_durations()
        self.gym_env.average_reward_per_episode.pop(0)  # remove episode 0
        return {
            "total_episodes": self.gym_env.episode_counter,
            "total_time_steps": self.gym_env.total_time_steps,
            "total_s": total_s,
            "s_per_step": s_per_step,
            "s_per_100_steps_10_nodes": s_per_100_steps_10_nodes,
            "av_reward_per_episode": self.gym_env.average_reward_per_episode,
        }


def _get_benchmark_primaite_environment() -> BenchmarkPrimaiteGymEnv:
    """
    Create an instance of the BenchmarkPrimaiteGymEnv.

    This environment will be used to train the agents on.
    """
    env = BenchmarkPrimaiteGymEnv(env_config=data_manipulation_config_path())
    return env


def _prepare_session_directory():
    """Prepare the session directory so that it is easier to clean up after the benchmarking is done."""
    # override session path
    session_path = _BENCHMARK_ROOT / "sessions"

    if session_path.is_dir():
        shutil.rmtree(session_path)

    primaite.PRIMAITE_PATHS.user_sessions_path = session_path
    primaite.PRIMAITE_PATHS.user_sessions_path.mkdir(exist_ok=True, parents=True)


def run(
    number_of_sessions: int = 5,
    num_episodes: int = 1000,
    episode_len: int = 128,
    n_steps: int = 1280,
    batch_size: int = 32,
    learning_rate: float = 3e-4,
) -> None:
    """Run the PrimAITE benchmark."""
    benchmark_start_time = datetime.now()

    session_metadata_dict = {}

    _prepare_session_directory()

    # run training
    for i in range(1, number_of_sessions + 1):
        print(f"Starting Benchmark Session: {i}")

        with _get_benchmark_primaite_environment() as gym_env:
            session = BenchmarkSession(
                gym_env=gym_env,
                num_episodes=num_episodes,
                n_steps=n_steps,
                episode_len=episode_len,
                batch_size=batch_size,
                learning_rate=learning_rate,
            )
            session.train()

            # Dump the session metadata so that we're not holding it in memory as it's large
            with open(_SESSION_METADATA_ROOT / f"{i}.json", "w") as file:
                json.dump(session.session_metadata, file, indent=4)

    for i in range(1, number_of_sessions + 1):
        with open(_SESSION_METADATA_ROOT / f"{i}.json", "r") as file:
            session_metadata_dict[i] = json.load(file)
    # generate report
    build_benchmark_latex_report(
        benchmark_start_time=benchmark_start_time,
        session_metadata=session_metadata_dict,
        config_path=data_manipulation_config_path(),
        results_root_path=_RESULTS_ROOT,
    )


if __name__ == "__main__":
    run()
