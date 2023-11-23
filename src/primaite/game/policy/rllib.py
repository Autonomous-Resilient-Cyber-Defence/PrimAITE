from pathlib import Path
from typing import Literal, Optional, TYPE_CHECKING

from primaite.game.policy.policy import PolicyABC
from primaite.session.environment import PrimaiteRayEnv

if TYPE_CHECKING:
    from primaite.session.session import PrimaiteSession, TrainingOptions

import ray
from ray.rllib.algorithms import ppo


class RaySingleAgentPolicy(PolicyABC, identifier="RLLIB_single_agent"):
    """Single agent RL policy using Ray RLLib."""

    def __init__(self, session: "PrimaiteSession", algorithm: Literal["PPO", "A2C"], seed: Optional[int] = None):
        super().__init__(session=session)

        config = {
            "env": PrimaiteRayEnv,
            "env_config": {"game": session.game},
            "disable_env_checking": True,
            "num_rollout_workers": 0,
        }

        ray.shutdown()
        ray.init()

        self._algo = ppo.PPO(config=config)

    def learn(self, n_episodes: int, timesteps_per_episode: int) -> None:
        """Train the agent."""
        for ep in range(n_episodes):
            self._algo.train()

    def eval(self, n_episodes: int, deterministic: bool) -> None:
        """Evaluate the agent."""
        for ep in range(n_episodes):
            obs, info = self.session.env.reset()
            for step in range(self.session.game.options.max_episode_length):
                action = self._algo.compute_single_action(observation=obs, explore=False)
                obs, rew, term, trunc, info = self.session.env.step(action)

    def save(self, save_path: Path) -> None:
        """Save the policy to a file."""
        self._algo.save(save_path)

    def load(self, model_path: Path) -> None:
        """Load policy parameters from a file."""
        raise NotImplementedError

    @classmethod
    def from_config(cls, config: "TrainingOptions", session: "PrimaiteSession") -> "RaySingleAgentPolicy":
        """Create a policy from a config."""
        return cls(session=session, algorithm=config.rl_algorithm, seed=config.seed)
