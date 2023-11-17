from pathlib import Path
from typing import Dict, List, Literal, Optional, SupportsFloat, Tuple, Type, TYPE_CHECKING, Union

import gymnasium
from gymnasium.core import ActType, ObsType

from primaite.game.environment import PrimaiteGymEnv
from primaite.game.policy.policy import PolicyABC

if TYPE_CHECKING:
    from primaite.game.agent.interface import ProxyAgent
    from primaite.game.session import PrimaiteSession, TrainingOptions

import ray
from ray.rllib.algorithms import Algorithm, ppo
from ray.rllib.algorithms.ppo import PPOConfig
from ray.tune.registry import register_env


class RaySingleAgentPolicy(PolicyABC, identifier="RLLIB_single_agent"):
    """Single agent RL policy using Ray RLLib."""

    def __init__(self, session: "PrimaiteSession", algorithm: Literal["PPO", "A2C"], seed: Optional[int] = None):
        super().__init__(session=session)
        ray.init()

        class RayPrimaiteGym(gymnasium.Env):
            def __init__(self, env_config: Dict) -> None:
                self.action_space = session.env.action_space
                self.observation_space = session.env.observation_space

            def reset(self, *, seed: int = None, options: dict = None) -> Tuple[ObsType, Dict]:
                obs, info = session.env.reset()
                return obs, info

            def step(self, action: ActType) -> Tuple[ObsType, SupportsFloat, bool, bool, Dict]:
                obs, reward, terminated, truncated, info = session.env.step(action)
                return obs, reward, terminated, truncated, info

        ray.shutdown()
        ray.init()

        config = {
            "env": RayPrimaiteGym,
            "env_config": {},
            "disable_env_checking": True,
            "num_rollout_workers": 0,
        }

        self._algo = ppo.PPO(config=config)

        # self._agent_config = (PPOConfig()
        # .update_from_dict({
        #     "num_gpus":0,
        #     "num_workers":0,
        #     "batch_mode":"complete_episodes",
        #     "framework":"torch",
        # })
        # .environment(
        #     env="primaite",
        #     env_config={"session": session, "agents": session.rl_agents,},
        #     # disable_env_checking=True
        #     )
        # # .rollouts(num_rollout_workers=0,
        #         #   num_envs_per_worker=0)
        # # .framework("tf2")
        # .evaluation(evaluation_num_workers=0)
        # )

        # self._agent:Algorithm = self._agent_config.build(use_copy=False)

    def learn(self, n_episodes: int, timesteps_per_episode: int) -> None:
        """Train the agent."""

        for ep in range(n_episodes):
            res = self._algo.train()
            print(f"Episode {ep} complete, reward: {res['episode_reward_mean']}")

    def eval(self, n_episodes: int, deterministic: bool) -> None:
        raise NotImplementedError

    def save(self, save_path: Path) -> None:
        raise NotImplementedError

    def load(self, model_path: Path) -> None:
        raise NotImplementedError

    @classmethod
    def from_config(cls, config: "TrainingOptions", session: "PrimaiteSession") -> "RaySingleAgentPolicy":
        """Create a policy from a config."""
        return cls(session=session, algorithm=config.rl_algorithm, seed=config.seed)
