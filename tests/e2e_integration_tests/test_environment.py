import pydantic
import pytest
import yaml
from gymnasium.core import ObsType
from numpy import ndarray

from primaite.session.environment import PrimaiteGymEnv, PrimaiteRayMARLEnv
from primaite.simulator.network.hardware.nodes.host.server import Printer
from primaite.simulator.network.hardware.nodes.network.wireless_router import WirelessRouter
from tests import TEST_ASSETS_ROOT

CFG_PATH = TEST_ASSETS_ROOT / "configs/test_primaite_session.yaml"
TRAINING_ONLY_PATH = TEST_ASSETS_ROOT / "configs/train_only_primaite_session.yaml"
EVAL_ONLY_PATH = TEST_ASSETS_ROOT / "configs/eval_only_primaite_session.yaml"
MISCONFIGURED_PATH = TEST_ASSETS_ROOT / "configs/bad_primaite_session.yaml"
MULTI_AGENT_PATH = TEST_ASSETS_ROOT / "configs/multi_agent_session.yaml"


class TestPrimaiteEnvironment:
    def test_creating_env(self):
        """Check that environment loads correctly from config and it can be reset."""
        with open(CFG_PATH, "r") as f:
            cfg = yaml.safe_load(f)
        env = PrimaiteGymEnv(env_config=cfg)

        def env_checks():
            assert env is not None
            assert env.game.simulation
            assert len(env.game.agents) == 3
            assert len(env.game.rl_agents) == 1

            assert env.game.simulation.network
            assert len(env.game.simulation.network.nodes) == 12
            wireless = env.game.simulation.network.get_node_by_hostname("router_2")
            assert isinstance(wireless, WirelessRouter)
            printer = env.game.simulation.network.get_node_by_hostname("HP_LaserJet_Pro_4102fdn_printer")
            assert isinstance(printer, Printer)

        env_checks()
        env.reset()
        env_checks()

    def test_step_env(self):
        """Make sure you can go all the way through the session without errors."""
        with open(CFG_PATH, "r") as f:
            cfg = yaml.safe_load(f)
        env = PrimaiteGymEnv(env_config=cfg)

        assert (num_actions := len(env.agent.action_manager.action_map)) == 54
        # run every action and make sure there's no crash
        for act in range(num_actions):
            env.step(act)
        # try running action number outside the action map to check that it fails.
        with pytest.raises(KeyError):
            env.step(num_actions)

        obs, rew, trunc, term, info = env.step(0)
        assert isinstance(obs, ndarray)

    def test_multi_agent_env(self):
        """Check that we can run a training session with a multi agent system."""
        with open(MULTI_AGENT_PATH, "r") as f:
            cfg = yaml.safe_load(f)
        env = PrimaiteRayMARLEnv(env_config=cfg)

        assert set(env._agent_ids) == {"defender1", "defender2"}

        assert len(env.agents) == 2
        defender1 = env.agents["defender1"]
        defender2 = env.agents["defender2"]
        assert (num_actions_1 := len(defender1.action_manager.action_map)) == 54
        assert (num_actions_2 := len(defender2.action_manager.action_map)) == 38

        # ensure we can run all valid actions without error
        for act_1 in range(num_actions_1):
            env.step({"defender1": act_1, "defender2": 0})
        for act_2 in range(num_actions_2):
            env.step({"defender1": 0, "defender2": act_2})

        # ensure we get error when taking an invalid action
        with pytest.raises(KeyError):
            env.step({"defender1": num_actions_1, "defender2": 0})
        with pytest.raises(KeyError):
            env.step({"defender1": 0, "defender2": num_actions_2})

    def test_error_thrown_on_bad_configuration(self):
        """Make sure we throw an error when the config is bad."""
        with open(MISCONFIGURED_PATH, "r") as f:
            cfg = yaml.safe_load(f)
        with pytest.raises(pydantic.ValidationError):
            env = PrimaiteGymEnv(env_config=cfg)
