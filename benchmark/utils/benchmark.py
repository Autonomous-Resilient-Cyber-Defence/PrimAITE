from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from gymnasium.core import ObsType

from primaite.session.environment import PrimaiteGymEnv


class BenchmarkPrimaiteGymEnv(PrimaiteGymEnv):
    """
    Class that extends the PrimaiteGymEnv.

    The reset method is extended so that the average rewards per episode are recorded.
    """

    total_time_steps: int = 0

    def reset(self, seed: Optional[int] = None) -> Tuple[ObsType, Dict[str, Any]]:
        """Overrides the PrimAITEGymEnv reset so that the total timesteps is saved."""
        self.total_time_steps += self.game.step_counter

        return super().reset(seed=seed)


#####################################
# IGNORE BELOW FOR NOW
#####################################


class BenchMarkOSInfo:
    """Operating System Information about the machine that run the benchmark."""

    operating_system: str
    """The operating system the benchmark was run on."""

    operating_system_version: str
    """The operating system version the benchmark was run on."""

    machine: str
    """The type of machine running the benchmark."""

    processor: str
    """The processor used to run the benchmark."""


class BenchMarkCPUInfo:
    """CPU Information of the machine that ran the benchmark."""

    physical_cores: int
    """The number of CPU cores the machine that ran the benchmark had."""

    total_cores: int
    """The number of total cores the machine that run the benchmark had."""

    max_frequency: int
    """The CPU's maximum clock speed."""


class BenchMarkMemoryInfo:
    """The Memory Information of the machine that ran the benchmark."""

    total: str
    """The total amount of memory."""

    swap_total: str
    """Virtual memory."""


class BenchMarkGPUInfo:
    """The GPU Information of the machine that ran the benchmark."""

    name: str
    """GPU name."""

    total_memory: str
    """GPU memory."""


class BenchMarkSystemInfo:
    """Overall system information of the machine that ran the benchmark."""

    system: BenchMarkOSInfo
    cpu: BenchMarkCPUInfo
    memory: BenchMarkMemoryInfo
    gpu: List[BenchMarkMemoryInfo]


class BenchMarkResult:
    """Class containing the relevant benchmark results."""

    benchmark_start_time: datetime
    """Start time of the benchmark run."""

    benchmark_end_time: datetime
    """End time of the benchmark run."""

    primaite_version: str
    """The version of PrimAITE being benchmarked."""

    system_info: BenchMarkSystemInfo
    """System information of the machine that ran the benchmark."""

    total_sessions: int
    """The number of sessions that the benchmark ran."""

    total_episodes: int
    """The number of episodes over all the sessions that the benchmark ran."""

    total_timesteps: int
    """The number of timesteps over all the sessions that the benchmark ran."""

    average_seconds_per_session: float
    """The average time per session."""

    average_seconds_per_step: float
    """The average time per step."""

    average_seconds_per_100_steps_and_10_nodes: float
    """The average time per 100 steps on a 10 node network."""

    combined_average_reward_per_episode: Dict
    """tbd."""
