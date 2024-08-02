from primaite.config.load import data_manipulation_config_path
from primaite.session.environment import PrimaiteGymEnv
from primaite.game.agent.interface import AgentHistoryItem
import yaml
from pprint import pprint
import pytest

@pytest.fixture()
def create_env():
    with open(data_manipulation_config_path(), 'r') as f:
        cfg = yaml.safe_load(f)

    env = PrimaiteGymEnv(env_config = cfg)
    return env

def test_rng_seed_set(create_env):
    env = create_env
    env.reset(seed=3)
    for i in range(100):
        env.step(0)
    a = [item.timestep for item in env.game.agents['client_2_green_user'].history if item.action!="DONOTHING"]

    env.reset(seed=3)
    for i in range(100):
        env.step(0)
    b = [item.timestep for item in env.game.agents['client_2_green_user'].history if item.action!="DONOTHING"]

    assert a==b

def test_rng_seed_unset(create_env):
    env = create_env
    env.reset()
    for i in range(100):
        env.step(0)
    a = [item.timestep for item in env.game.agents['client_2_green_user'].history if item.action!="DONOTHING"]

    env.reset()
    for i in range(100):
        env.step(0)
    b = [item.timestep for item in env.game.agents['client_2_green_user'].history if item.action!="DONOTHING"]

    assert a!=b

