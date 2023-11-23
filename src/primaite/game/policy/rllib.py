from pathlib import Path
from typing import Literal, Optional, TYPE_CHECKING

from primaite.game.policy.policy import PolicyABC
from primaite.session.environment import PrimaiteRayEnv, PrimaiteRayMARLEnv

if TYPE_CHECKING:
    from primaite.session.session import PrimaiteSession, TrainingOptions

import ray
from ray import air, tune
from ray.rllib.algorithms import ppo
from ray.rllib.algorithms.ppo import PPOConfig


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


class RayMultiAgentPolicy(PolicyABC, identifier="RLLIB_multi_agent"):
    """Mutli agent RL policy using Ray RLLib."""

    def __init__(self, session: "PrimaiteSession", algorithm: Literal["PPO"], seed: Optional[int] = None):
        """Initialise multi agent policy wrapper."""
        super().__init__(session=session)

        self.config = (
            PPOConfig()
            .environment(env=PrimaiteRayMARLEnv, env_config={"game": session.game})
            .rollouts(num_rollout_workers=0)
            .multi_agent(
                policies={agent.agent_name for agent in session.game.rl_agents},
                policy_mapping_fn=lambda agent_id, episode, worker, **kw: agent_id,
            )
            .training(train_batch_size=128)
        )

    def learn(self, n_episodes: int, timesteps_per_episode: int) -> None:
        """Train the agent."""
        tune.Tuner(
            "PPO",
            run_config=air.RunConfig(
                stop={"training_iteration": n_episodes * timesteps_per_episode},
                checkpoint_config=air.CheckpointConfig(checkpoint_frequency=10),
            ),
            param_space=self.config,
        ).fit()

    def load(self, model_path: Path) -> None:
        """Load policy paramters from a file."""
        return NotImplemented

    def eval(self, n_episodes: int, deterministic: bool) -> None:
        """Evaluate trained policy."""
        return NotImplemented

    def save(self, save_path: Path) -> None:
        """Save policy parameters to a file."""
        return NotImplemented

    @classmethod
    def from_config(cls, config: "TrainingOptions", session: "PrimaiteSession") -> "RayMultiAgentPolicy":
        """Create policy from config."""
        return cls(session=session, algorithm=config.rl_algorithm, seed=config.seed)
