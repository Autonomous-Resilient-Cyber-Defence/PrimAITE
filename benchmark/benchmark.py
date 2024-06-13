from typing import Any, Dict, Optional, Tuple

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
