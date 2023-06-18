from typing import Optional

from stable_baselines3 import PPO

from primaite.agents.agent_abc import AgentABC
from primaite.environment.primaite_env import Primaite
from stable_baselines3.ppo import MlpPolicy as PPOMlp


class SB3PPO(AgentABC):
    def __init__(
            self,
            training_config_path,
            lay_down_config_path
    ):
        super().__init__(training_config_path, lay_down_config_path)
        self._tensorboard_log_path = self.session_path / "tensorboard_logs"
        self._tensorboard_log_path.mkdir(parents=True, exist_ok=True)

    def _setup(self):
        self._env = Primaite(
            training_config_path=self._training_config_path,
            lay_down_config_path=self._lay_down_config_path,
            transaction_list=[],
            session_path=self.session_path,
            timestamp_str=self.timestamp_str
        )
        self._agent = PPO(
            PPOMlp,
            self._env,
            verbose=0,
            n_steps=self._training_config.num_steps,
            tensorboard_log=self._tensorboard_log_path
        )

    def learn(
            self,
            time_steps: Optional[int] = None,
            episodes: Optional[int] = None
    ):
        if not time_steps:
            time_steps = self._training_config.num_steps

        if not episodes:
            episodes = self._training_config.num_episodes

        for i in range(episodes):
            self._agent.learn(total_timesteps=time_steps)

    def evaluate(
            self,
            time_steps: Optional[int] = None,
            episodes: Optional[int] = None,
            deterministic: bool = True
    ):
        if not time_steps:
            time_steps = self._training_config.num_steps

        if not episodes:
            episodes = self._training_config.num_episodes

        for episode in range(episodes):
            obs = self._env.reset()

            for step in range(time_steps):
                action, _states = self._agent.predict(
                    obs,
                    deterministic=deterministic
                )
                obs, rewards, done, info = self._env.step(action)

    def load(self):
        raise NotImplementedError

    def save(self):
        raise NotImplementedError

    def export(self):
        raise NotImplementedError
