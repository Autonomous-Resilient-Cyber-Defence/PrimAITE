from enum import Enum
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict

from primaite.game.environment import PrimaiteGymEnv

# from primaite.game.game import PrimaiteGame
from primaite.game.policy.policy import PolicyABC
from primaite.session.io import SessionIO, SessionIOSettings


class TrainingOptions(BaseModel):
    """Options for training the RL agent."""

    model_config = ConfigDict(extra="forbid")

    rl_framework: Literal["SB3", "RLLIB_single_agent"]
    rl_algorithm: Literal["PPO", "A2C"]
    n_learn_episodes: int
    n_eval_episodes: Optional[int] = None
    max_steps_per_episode: int
    # checkpoint_freq: Optional[int] = None
    deterministic_eval: bool
    seed: Optional[int]
    n_agents: int
    agent_references: List[str]


class SessionMode(Enum):
    """Helper to keep track of the current session mode."""

    TRAIN = "train"
    EVAL = "eval"
    MANUAL = "manual"


class PrimaiteSession:
    """The main entrypoint for PrimAITE sessions, this manages a simulation, policy training, and environments."""

    def __init__(self):
        """Initialise PrimaiteSession object."""
        self.training_options: TrainingOptions
        """Options specific to agent training."""

        self.mode: SessionMode = SessionMode.MANUAL
        """Current session mode."""

        self.env: PrimaiteGymEnv
        """The environment that the agent can consume. Could be PrimaiteEnv."""

        self.policy: PolicyABC
        """The reinforcement learning policy."""

        self.io_manager = SessionIO()
        """IO manager for the session."""

    def start_session(self) -> None:
        """Commence the training/eval session."""
        self.mode = SessionMode.TRAIN
        n_learn_episodes = self.training_options.n_learn_episodes
        n_eval_episodes = self.training_options.n_eval_episodes
        max_steps_per_episode = self.training_options.max_steps_per_episode

        deterministic_eval = self.training_options.deterministic_eval
        self.policy.learn(
            n_episodes=n_learn_episodes,
            timesteps_per_episode=max_steps_per_episode,
        )
        self.save_models()

        self.mode = SessionMode.EVAL
        if n_eval_episodes > 0:
            self.policy.eval(n_episodes=n_eval_episodes, deterministic=deterministic_eval)

        self.mode = SessionMode.MANUAL

    def save_models(self) -> None:
        """Save the RL models."""
        save_path = self.io_manager.generate_model_save_path("temp_model_name")
        self.policy.save(save_path)

    @classmethod
    def from_config(cls, cfg: Dict, agent_load_path: Optional[str] = None) -> "PrimaiteSession":
        """Create a PrimaiteSession object from a config dictionary."""
        sess = cls()

        sess.training_options = TrainingOptions(**cfg["training_config"])

        # READ IO SETTINGS (this sets the global session path as well) # TODO: GLOBAL SIDE EFFECTS...
        io_settings = cfg.get("io_settings", {})
        sess.io_manager.settings = SessionIOSettings(**io_settings)
