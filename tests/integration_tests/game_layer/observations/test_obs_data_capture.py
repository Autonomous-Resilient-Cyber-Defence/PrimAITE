# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
import json

from primaite.session.environment import PrimaiteGymEnv
from primaite.session.io import PrimaiteIO
from tests import TEST_ASSETS_ROOT

DATA_MANIPULATION_CONFIG = TEST_ASSETS_ROOT / "configs" / "data_manipulation.yaml"


def test_obs_data_in_log_file():
    """Create a log file of AgentHistoryItems and check observation data is
    included. Assumes that data_manipulation.yaml has an agent labelled
    'defender' with a non-null observation space.
    The log file will be in:
        primaite/VERSION/sessions/YYYY-MM-DD/HH-MM-SS/agent_actions
    """
    env = PrimaiteGymEnv(DATA_MANIPULATION_CONFIG)
    env.reset()
    for _ in range(10):
        env.step(0)
    env.reset()
    io = PrimaiteIO()
    path = io.generate_agent_actions_save_path(episode=1)
    with open(path, "r") as f:
        j = json.load(f)

    assert type(j["0"]["defender"]["observation"]) == dict
