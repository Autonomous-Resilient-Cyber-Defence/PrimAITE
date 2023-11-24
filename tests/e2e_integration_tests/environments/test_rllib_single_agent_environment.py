import tempfile
from pathlib import Path

import ray
import yaml
from ray.rllib.algorithms import ppo

from primaite.config.load import example_config_path
from primaite.game.game import PrimaiteGame
from primaite.session.environment import PrimaiteRayEnv


def test_rllib_single_agent_compatibility():
    """Test that the PrimaiteRayEnv class can be used with a single agent RLLIB system."""
    with open(example_config_path(), "r") as f:
        cfg = yaml.safe_load(f)

    game = PrimaiteGame.from_config(cfg)

    ray.shutdown()
    ray.init()

    env_config = {"game": game}
    config = {
        "env": PrimaiteRayEnv,
        "env_config": env_config,
        "disable_env_checking": True,
        "num_rollout_workers": 0,
    }

    algo = ppo.PPO(config=config)

    for i in range(5):
        result = algo.train()

    save_file = Path(tempfile.gettempdir()) / "ray/"
    algo.save(save_file)
    assert save_file.exists()
