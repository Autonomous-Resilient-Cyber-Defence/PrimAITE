# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from pprint import pprint

import pytest
import yaml

from primaite.config.load import data_manipulation_config_path
from primaite.game.agent.interface import AgentHistoryItem
from primaite.session.environment import PrimaiteGymEnv
from primaite.simulator import SIM_OUTPUT


@pytest.fixture()
def create_env():
    with open(data_manipulation_config_path(), "r") as f:
        cfg = yaml.safe_load(f)

    env = PrimaiteGymEnv(env_config=cfg)
    return env


def test_rng_seed_set(create_env):
    """Test with RNG seed set."""
    env = create_env
    env.reset(seed=3)
    for i in range(100):
        env.step(0)
    a = [item.timestep for item in env.game.agents["client_2_green_user"].history if item.action != "do-nothing"]

    env.reset(seed=3)
    for i in range(100):
        env.step(0)
    b = [item.timestep for item in env.game.agents["client_2_green_user"].history if item.action != "do-nothing"]

    assert a == b

    # Check that seed log file was created.
    path = SIM_OUTPUT.path / "seed.log"
    with open(path, "r") as file:
        assert file


def test_rng_seed_unset(create_env):
    """Test with no RNG seed."""
    env = create_env
    env.reset()
    for i in range(100):
        env.step(0)
    a = [item.timestep for item in env.game.agents["client_2_green_user"].history if item.action != "do-nothing"]

    env.reset()
    for i in range(100):
        env.step(0)
    b = [item.timestep for item in env.game.agents["client_2_green_user"].history if item.action != "do-nothing"]

    assert a != b


def test_for_generated_seed():
    """
    Show that setting generate_seed_value to true producess a valid seed.
    """
    with open(data_manipulation_config_path(), "r") as f:
        cfg = yaml.safe_load(f)

    cfg["game"]["generate_seed_value"] = True
    PrimaiteGymEnv(env_config=cfg)
    path = SIM_OUTPUT.path / "seed.log"
    with open(path, "r") as file:
        data = file.read()

    assert data.split(" ")[3] != None
