# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
import pytest
import yaml

from primaite.session.environment import PrimaiteGymEnv
from primaite.session.ray_envs import PrimaiteRayEnv, PrimaiteRayMARLEnv
from primaite.simulator.network.hardware.nodes.network.wireless_router import WirelessRouter
from tests.conftest import TEST_ASSETS_ROOT

folder_path = TEST_ASSETS_ROOT / "configs" / "scenario_with_placeholders"
single_yaml_config = TEST_ASSETS_ROOT / "configs" / "test_primaite_session.yaml"
with open(single_yaml_config, "r") as f:
    config_dict = yaml.safe_load(f)


@pytest.mark.parametrize("env_type", [PrimaiteGymEnv, PrimaiteRayEnv, PrimaiteRayMARLEnv])
def test_creating_env_with_folder(env_type):
    """Check that the environment can be created with a folder path."""

    def check_taking_steps(e):
        if isinstance(e, PrimaiteRayMARLEnv):
            for i in range(9):
                e.step({k: i for k in e.game.rl_agents})
        else:
            for i in range(9):
                e.step(i)

    env = env_type(env_config=folder_path)
    assert env is not None
    for _ in range(3):  # do it multiple times to ensure it loops back to the beginning
        assert len(env.game.agents) == 1
        assert "defender" in env.game.agents
        check_taking_steps(env)

        env.reset()
        assert len(env.game.agents) == 2
        assert "defender" in env.game.agents
        assert "red_A" in env.game.agents
        check_taking_steps(env)

        env.reset()
        assert len(env.game.agents) == 3
        assert all([a in env.game.agents for a in ["defender", "green_A", "red_A"]])
        check_taking_steps(env)

        env.reset()
        assert len(env.game.agents) == 3
        assert all([a in env.game.agents for a in ["defender", "green_B", "red_B"]])
        check_taking_steps(env)

        env.reset()


@pytest.mark.parametrize(
    "env_data, env_type",
    [
        (single_yaml_config, PrimaiteGymEnv),
        (single_yaml_config, PrimaiteRayEnv),
        (single_yaml_config, PrimaiteRayMARLEnv),
        (config_dict, PrimaiteGymEnv),
        (config_dict, PrimaiteRayEnv),
        (config_dict, PrimaiteRayMARLEnv),
    ],
)
def test_creating_env_with_static_config(env_data, env_type):
    """Check that the environment can be created with a single yaml file."""
    env = env_type(env_config=single_yaml_config)
    assert env is not None
    agents_before = len(env.game.agents)
    env.reset()
    assert len(env.game.agents) == agents_before
