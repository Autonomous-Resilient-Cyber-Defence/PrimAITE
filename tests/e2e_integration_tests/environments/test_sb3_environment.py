"""Test that we can create a primaite environment and train sb3 agent with no crash."""
import tempfile
from pathlib import Path

import yaml
from stable_baselines3 import PPO

from primaite.config.load import example_config_path
from primaite.game.game import PrimaiteGame
from primaite.session.environment import PrimaiteGymEnv


def test_sb3_compatibility():
    """Test that the Gymnasium environment can be used with an SB3 agent."""
    with open(example_config_path(), "r") as f:
        cfg = yaml.safe_load(f)

    game = PrimaiteGame.from_config(cfg)
    gym = PrimaiteGymEnv(game=game)
    model = PPO("MlpPolicy", gym)

    model.learn(total_timesteps=1000)

    save_path = Path(tempfile.gettempdir()) / "model.zip"
    model.save(save_path)

    assert (save_path).exists()
