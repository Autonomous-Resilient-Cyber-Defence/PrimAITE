from typing import Literal, TYPE_CHECKING, Union

from stable_baselines3 import A2C, PPO
from stable_baselines3.a2c import MlpPolicy as A2C_MLP
from stable_baselines3.ppo import MlpPolicy as PPO_MLP

from primaite.game.policy.policy import PolicyABC

if TYPE_CHECKING:
    from primaite.game.session import PrimaiteSession


class SB3Policy(PolicyABC):
    """Single agent RL policy using stable baselines 3."""

    def __init__(self, session: "PrimaiteSession", algorithm: Literal["PPO", "A2C"]):
        """Initialize a stable baselines 3 policy."""
        super().__init__(session=session)

        self._agent_class: type[Union[PPO, A2C]]
        if algorithm == "PPO":
            self._agent_class = PPO
            policy = PPO_MLP
        elif algorithm == "A2C":
            self._agent_class = A2C
            policy = A2C_MLP
        else:
            raise ValueError(f"Unknown algorithm `{algorithm}` for stable_baselines3 policy")
        self._agent = self._agent_class(
            policy=policy,
            env=self.session.env,
            n_steps=...,
            seed=...,
        )  # TODO: populate values once I figure out how to get them from the config / session

    def learn(self, n_episodes: int, n_time_steps: int) -> None:
        """Train the agent."""
        # TODO: consider moving this loop to the session, only if this makes sense for RAY RLLIB
        for i in range(n_episodes):
            self._agent.learn(total_timesteps=n_time_steps)
            self._save_checkpoint()
        pass

    def eval(self, n_episodes: int, n_time_steps: int, deterministic: bool) -> None:
        """Evaluate the agent."""
        # TODO: consider moving this loop to the session, only if this makes sense for RAY RLLIB
        for episode in range(n_episodes):
            obs = self.session.env.reset()
            for step in range(n_time_steps):
                action, _states = self._agent.predict(obs, deterministic=deterministic)
                obs, rewards, truncated, terminated, info = self.session.env.step(action)

    def save(self) -> None:
        """Save the agent."""
        savepath = (
            "temp/path/to/save.pth"  # TODO: populate values once I figure out how to get them from the config / session
        )
        self._agent.save(savepath)
        pass

    def load(self) -> None:
        """Load agent from a checkpoint."""
        self._agent_class.load("temp/path/to/save.pth", env=self.session.env)
        pass

    def close(self) -> None:
        """Close the agent."""
        pass

    @classmethod
    def from_config(self) -> "SB3Policy":
        """Create an agent from config file."""
        pass
