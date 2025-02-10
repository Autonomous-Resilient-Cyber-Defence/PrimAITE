# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
import pytest
import yaml

from primaite.config.load import _EXAMPLE_CFG
from primaite.game.agent.scripted_agents.abstract_tap import (
    AbstractTAP,
    BaseKillChain,
    KillChainOptions,
    KillChainStageOptions,
    KillChainStageProgress,
)
from primaite.game.agent.scripted_agents.TAP001 import MobileMalwareKillChain
from primaite.game.agent.scripted_agents.TAP003 import InsiderKillChain
from primaite.session.environment import PrimaiteGymEnv

# Defining constants.

START_STEP = 1  # The starting step of the agent.
FREQUENCY = 2  # The frequency of kill chain stage progression (E.g it's next attempt at "attacking").
VARIANCE = 0  # The timestep variance between kill chain progression (E.g Next timestep = Frequency +/- variance)


def uc7_tap003_env() -> PrimaiteGymEnv:
    """Setups the UC7 TAP003 Game with the start_step & frequency set to 1 with probabilities set to 1 as well"""
    with open(_EXAMPLE_CFG / "uc7_config_tap003.yaml", mode="r") as uc7_config:
        cfg = yaml.safe_load(uc7_config)
        cfg["io_settings"]["save_sys_logs"] = False
        cfg["agents"][32]["agent_settings"]["start_step"] = START_STEP
        cfg["agents"][32]["agent_settings"]["frequency"] = FREQUENCY
        cfg["agents"][32]["agent_settings"]["variance"] = VARIANCE
    env = PrimaiteGymEnv(env_config=cfg)
    return env


def uc7_tap001_env() -> PrimaiteGymEnv:
    """Setup the UC7 TAP001 Game with the start_step & frequency set to 1 & 2 respectively. Probabilities are set to 1"""
    with open(_EXAMPLE_CFG / "uc7_config.yaml", mode="r") as uc7_config:
        cfg = yaml.safe_load(uc7_config)
        cfg["io_settings"]["save_sys_logs"] = False
        cfg["agents"][32]["agent_settings"]["start_step"] = START_STEP
        cfg["agents"][32]["agent_settings"]["frequency"] = FREQUENCY
        cfg["agents"][32]["agent_settings"]["variance"] = VARIANCE
    env = PrimaiteGymEnv(env_config=cfg)
    return env


def test_tap003_insider_kill_chain_load():
    """Tests that tap003's insider kill chain is successfully loaded into the tap.selected_kill_chain attribute."""
    env = uc7_tap003_env()  # Using TAP003 for PyTests.
    tap: TAP003 = env.game.agents["attacker"]
    # Asserting that the Base Kill Chain intEnum stages are loaded
    assert BaseKillChain.FAILED in [enums for enums in tap.selected_kill_chain]
    assert BaseKillChain.SUCCEEDED in [enums for enums in tap.selected_kill_chain]
    assert BaseKillChain.NOT_STARTED in [enums for enums in tap.selected_kill_chain]
    # Asserting that the Insider Kill Chain intenum stages are loaded.
    assert len(InsiderKillChain.__members__) == len(tap.selected_kill_chain.__members__)


def test_tap001_mobile_malware_kill_chain_load():
    """Tests that tap001's mobile malware is successfully loaded into the tap.selected_kill_chain attribute."""
    env = uc7_tap001_env()  # Using TAP003 for PyTests.
    tap: TAP001 = env.game.agents["attacker"]
    # Asserting that the Base Kill Chain intEnum stages are loaded.
    assert BaseKillChain.FAILED in [enums for enums in tap.selected_kill_chain]
    assert BaseKillChain.SUCCEEDED in [enums for enums in tap.selected_kill_chain]
    assert BaseKillChain.NOT_STARTED in [enums for enums in tap.selected_kill_chain]
    # Asserting that the Insider Kill Chain intEnum stages are loaded.
    assert len(MobileMalwareKillChain.__members__) == len(tap.selected_kill_chain.__members__)
