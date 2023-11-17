

from typing import Literal, Optional, Type, TYPE_CHECKING, Union

from primaite.game.policy import PolicyABC

if TYPE_CHECKING:
    from primaite.game.session import PrimaiteSession, TrainingOptions

from ray.rllib


class RaySingleAgentPolicy(PolicyABC, identifier="RLLIB_single_agent"):
    """Single agent RL policy using Ray RLLib."""

    def __init__(self, session: "PrimaiteSession", algorithm: Literal["PPO", "A2C"], seed: Optional[int] = None):
        super().__init__(session=session)

