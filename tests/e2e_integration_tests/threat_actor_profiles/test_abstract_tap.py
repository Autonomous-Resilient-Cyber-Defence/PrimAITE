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
from primaite.game.agent.scripted_agents.TAP001 import MobileMalwareKillChain, TAP001
from primaite.game.agent.scripted_agents.TAP003 import InsiderKillChain, TAP003
from primaite.session.environment import PrimaiteGymEnv

START_STEP = 1  # The starting step of the agent.
FREQUENCY = 5  # The frequency of kill chain stage progression (E.g it's next attempt at "attacking").
VARIANCE = 0  # The timestep variance between kill chain progression (E.g Next timestep = Frequency +/- variance)
ATTACK_AGENT_INDEX = 32


def uc7_tap001_env() -> PrimaiteGymEnv:
    with open(_EXAMPLE_CFG / "uc7_config.yaml", mode="r") as uc7_config:
        cfg = yaml.safe_load(uc7_config)
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["start_step"] = START_STEP
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["frequency"] = FREQUENCY
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["variance"] = VARIANCE

    env = PrimaiteGymEnv(env_config=cfg)

    return env


def uc7_tap003_env(**kwargs) -> PrimaiteGymEnv:
    """Setups the UC7 TAP003 Game with the following settings:

    start_step = Start on Step 1
    frequency = Attack Every 5 Steps

    Each PyTest will define the rest of the TAP & Kill Chain settings via **Kwargs
    """
    with open(_EXAMPLE_CFG / "uc7_config_tap003.yaml", "r") as uc7_config:
        cfg = yaml.safe_load(uc7_config)
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["start_step"] = START_STEP
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["frequency"] = FREQUENCY
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["variance"] = VARIANCE

    if "repeat_kill_chain" in kwargs:
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["repeat_kill_chain"] = kwargs["repeat_kill_chain"]
    if "repeat_kill_chain_stages" in kwargs:
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["repeat_kill_chain_stages"] = kwargs[
            "repeat_kill_chain_stages"
        ]
    if "planning_probability" in kwargs:
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["kill_chain"]["PLANNING"]["probability"] = kwargs[
            "planning_probability"
        ]
    if "custom_kill_chain" in kwargs:
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["kill_chain"] = kwargs["custom_kill_chain"]
    if "starting_nodes" in kwargs:
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["starting_nodes"] = kwargs["starting_nodes"]
    if "target_nodes" in kwargs:
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["target_nodes"] = kwargs["target_nodes"]

    env = PrimaiteGymEnv(env_config=cfg)
    return env


def test_tap001_setup():
    """Tests abstract TAP's following methods:
    1. _setup_kill_chain
    2. _setup_agent_kill_chain
    3. _setup_tap_applications
    """
    env = uc7_tap001_env()  # Using TAP001 for PyTests.
    tap: TAP001 = env.game.agents["attacker"]

    # check the kill chain loaded correctly
    assert tap.selected_kill_chain is MobileMalwareKillChain
    assert tap.selected_kill_chain.FAILED == BaseKillChain.FAILED
    assert tap.selected_kill_chain.SUCCEEDED == BaseKillChain.SUCCEEDED
    assert tap.selected_kill_chain.NOT_STARTED == BaseKillChain.NOT_STARTED

    if sn := tap.config.agent_settings.default_starting_node:
        assert tap.starting_node == sn
    else:
        assert tap.starting_node in tap.config.agent_settings.starting_nodes

    if ti := tap.config.agent_settings.default_target_ip:
        assert tap.target_ip == ti
    else:
        assert tap.target_ip in tap.config.agent_settings.target_ips

    assert tap.next_execution_timestep == tap.config.agent_settings.start_step

    assert tap.current_host == tap.starting_node


def test_abstract_tap_select_start_node():
    """Tests that Abstract TAP's _select_start_node"""
    env = uc7_tap003_env(repeat_kill_chain=True, repeat_kill_chain_stages=True)  # Using TAP003 for PyTests.
    tap: TAP003 = env.game.agents["attacker"]

    assert tap.starting_node == "ST_PROJ-A-PRV-PC-1"
    assert tap.current_host == tap.starting_node


def test_outcome_handler():
    """Tests Abstract Tap's outcome handler concludes the episode when the kill chain fails."""
    env = uc7_tap003_env(repeat_kill_chain=False, repeat_kill_chain_stages=False)  # Using TAP003 for PyTests.
    tap: TAP003 = env.game.agents["attacker"]
    tap.current_kill_chain_stage = BaseKillChain.FAILED
    # 6 Iterations as the attacker frequency is set to 5. Therefore, after 6 timesteps we expect the agent to realise it's failed the kill chain.
    for _ in range(6):
        env.step(0)
    assert tap.actions_concluded == True


def test_abstract_tap_kill_chain_repeat():
    """Tests that the kill chain repeats from the beginning upon failure."""
    env = uc7_tap003_env(repeat_kill_chain=True, repeat_kill_chain_stages=False)  # Using TAP003 for PyTests.
    tap: TAP003 = env.game.agents["attacker"]
    for _ in range(15):
        env.step(0)  # Steps directly to the Access Stage
    assert tap.current_kill_chain_stage == InsiderKillChain.ACCESS
    tap.current_kill_chain_stage = BaseKillChain.FAILED
    for _ in range(5):
        env.step(0)  # Steps to manipulation - but failure causes the kill chain to restart.
    assert tap.actions_concluded == False
    assert tap.current_kill_chain_stage == InsiderKillChain.RECONNAISSANCE

    """Tests that kill chain stages repeat when expected"""
    env = uc7_tap003_env(
        repeat_kill_chain=True, repeat_kill_chain_stages=True, planning_probability=0
    )  # Using TAP003 for PyTests.
    tap: TAP003 = env.game.agents["attacker"]
    tap.current_kill_chain_stage = InsiderKillChain.PLANNING
    for _ in range(15):
        env.step(0)  #  Attempts to progress past the PLANNING stage multiple times.
    assert tap.actions_concluded == False
    assert tap.current_kill_chain_stage == InsiderKillChain.PLANNING
