import ray
import yaml
from ray import air, tune
from ray.rllib.algorithms.ppo import PPOConfig

from primaite.session.ray_envs import PrimaiteRayMARLEnv
from tests import TEST_ASSETS_ROOT

MULTI_AGENT_PATH = TEST_ASSETS_ROOT / "configs/multi_agent_session.yaml"


def test_rllib_multi_agent_compatibility():
    """Test that the PrimaiteRayEnv class can be used with a multi agent RLLIB system."""

    with open(MULTI_AGENT_PATH, "r") as f:
        cfg = yaml.safe_load(f)

    ray.init()

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

    tune.Tuner(
        "PPO",
        run_config=air.RunConfig(
            stop={"training_iteration": 128},
            checkpoint_config=air.CheckpointConfig(
                checkpoint_frequency=10,
            ),
        ),
        param_space=config,
    ).fit()
