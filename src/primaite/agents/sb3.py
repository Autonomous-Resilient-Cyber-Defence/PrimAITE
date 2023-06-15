from typing import Optional

from stable_baselines3 import PPO

from primaite.agents.agent_abc import AgentABC
from primaite.environment.primaite_env import Primaite
from stable_baselines3.ppo import MlpPolicy as PPOMlp

class SB3PPO(AgentABC):
    def __init__(self, env: Primaite):
        super().__init__(env)

    def _setup(self):
        self._agent = PPO(
            PPOMlp,
            self._env,
            verbose=0,
            n_steps=self._training_config.num_steps
        )


    def learn(self, time_steps: Optional[int], episodes: Optional[int]):
        pass

    def evaluate(self, time_steps: Optional[int], episodes: Optional[int]):
        pass

    def load(self):
        pass

    def save(self):
        pass

    def export(self):
        pass