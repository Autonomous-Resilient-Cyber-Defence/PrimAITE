# raise DeprecationWarning("This module is deprecated")
from enum import Enum
from pathlib import Path
from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict

from primaite.session.environment import PrimaiteGymEnv, PrimaiteRayEnv, PrimaiteRayMARLEnv
from primaite.session.io import PrimaiteIO

# from primaite.game.game import PrimaiteGame
from primaite.session.policy.policy import PolicyABC


class TrainingOptions(BaseModel):
    """Options for training the RL agent."""

    model_config = ConfigDict(extra="forbid")

    rl_framework: Literal["SB3", "RLLIB_single_agent", "RLLIB_multi_agent"]
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

    def __init__(self, game_cfg: Dict):
        """Initialise PrimaiteSession object."""
        self.training_options: TrainingOptions
        """Options specific to agent training."""

        self.mode: SessionMode = SessionMode.MANUAL
        """Current session mode."""

        self.env: Union[PrimaiteGymEnv, PrimaiteRayEnv, PrimaiteRayMARLEnv]
        """The environment that the RL algorithm can consume."""

        self.policy: PolicyABC
        """The reinforcement learning policy."""

        self.io_manager: Optional["PrimaiteIO"] = None
        """IO manager for the session."""

        self.game_cfg: Dict = game_cfg
        """Primaite Game object for managing main simulation loop and agents."""

        self.save_checkpoints: bool = False
        """Whether to save checkpoints."""

        self.checkpoint_interval: int = 10
        """If save_checkpoints is true, checkpoints will be saved every checkpoint_interval episodes."""

    def start_session(self) -> None:
        """Commence the training/eval session."""
        print("Starting Primaite Session")
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
        # READ IO SETTINGS (this sets the global session path as well) # TODO: GLOBAL SIDE EFFECTS...
        io_manager = PrimaiteIO.from_config(cfg.get("io_settings", {}))

        sess = cls(game_cfg=cfg)
        sess.io_manager = io_manager
        sess.training_options = TrainingOptions(**cfg["training_config"])
        sess.save_checkpoints = cfg.get("io_settings", {}).get("save_checkpoints")
        sess.checkpoint_interval = cfg.get("io_settings", {}).get("checkpoint_interval")

        # CREATE ENVIRONMENT
        if sess.training_options.rl_framework == "RLLIB_single_agent":
            sess.env = PrimaiteRayEnv(env_config=cfg)
        elif sess.training_options.rl_framework == "RLLIB_multi_agent":
            sess.env = PrimaiteRayMARLEnv(env_config=cfg)
        elif sess.training_options.rl_framework == "SB3":
            sess.env = PrimaiteGymEnv(game_config=cfg)

        sess.policy = PolicyABC.from_config(sess.training_options, session=sess)
        if agent_load_path:
            sess.policy.load(Path(agent_load_path))

        return sess
