import ray
import yaml
from ray import air, tune
from ray.rllib.algorithms.ppo import PPOConfig

from primaite.config.load import example_config_path
from primaite.game.game import PrimaiteGame
from primaite.session.environment import PrimaiteRayMARLEnv


def test_rllib_multi_agent_compatibility():
    """Test that the PrimaiteRayEnv class can be used with a multi agent RLLIB system."""

    with open(example_config_path(), "r") as f:
        cfg = yaml.safe_load(f)

    game = PrimaiteGame.from_config(cfg)

    ray.shutdown()
    ray.init()

    env_config = {"game": game}
    config = (
        PPOConfig()
        .environment(env=PrimaiteRayMARLEnv, env_config={"game": game})
        .rollouts(num_rollout_workers=0)
        .multi_agent(
            policies={agent.agent_name for agent in game.rl_agents},
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
