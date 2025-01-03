# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
import yaml
from ray.rllib.algorithms.ppo import PPOConfig

from primaite.session.ray_envs import PrimaiteRayMARLEnv
from tests import TEST_ASSETS_ROOT

MULTI_AGENT_PATH = TEST_ASSETS_ROOT / "configs/multi_agent_session.yaml"


def test_rllib_multi_agent_compatibility():
    """Test that the PrimaiteRayEnv class can be used with a multi agent RLLIB system."""
    with open(MULTI_AGENT_PATH, "r") as f:
        cfg = yaml.safe_load(f)

    config = (
        PPOConfig()
        .environment(env=PrimaiteRayMARLEnv, env_config=cfg)
        .rollouts(num_rollout_workers=0)
        .multi_agent(
            policies={agent["ref"] for agent in cfg["agents"]},
            policy_mapping_fn=lambda agent_id, episode, worker, **kw: agent_id,
        )
        .training(train_batch_size=128)
    )
    algo = config.build()
    algo.train()
