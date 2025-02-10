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


def uc7_tap001_env(**kwargs) -> PrimaiteGymEnv:
    """Setups the UC7 tap001 Game with the start_step & frequency set to 1 with probabilities set to 1 as well"""
    with open(_EXAMPLE_CFG / "uc7_config.yaml", mode="r") as uc7_config:
        cfg = yaml.safe_load(uc7_config)
        cfg["io_settings"]["save_sys_logs"] = False
        cfg["agents"][32]["agent_settings"]["start_step"] = START_STEP
        cfg["agents"][32]["agent_settings"]["frequency"] = FREQUENCY
        cfg["agents"][32]["agent_settings"]["variance"] = VARIANCE
        cfg["agents"][32]["agent_settings"]["repeat_kill_chain"] = kwargs["repeat_kill_chain"]
        cfg["agents"][32]["agent_settings"]["repeat_kill_chain_stages"] = kwargs["repeat_kill_chain_stages"]
        cfg["agents"][32]["agent_settings"]["kill_chain"]["PROPAGATE"]["probability"] = kwargs["propagate_probability"]
        cfg["agents"][32]["agent_settings"]["kill_chain"]["PAYLOAD"]["probability"] = kwargs["payload_probability"]
    env = PrimaiteGymEnv(env_config=cfg)
    return env


def test_tap001_repeating_kill_chain():
    """Tests to check that tap001 repeats it's kill chain after success"""
    env = uc7_tap001_env(
        repeat_kill_chain=True,
        repeat_kill_chain_stages=True,
        payload_probability=1,
        propagate_probability=1,
    )
    tap001: TAP001 = env.game.agents["attacker"]
    # Looping for 50 timesteps - As the agent is set to execute an action every 2 timesteps
    # This is the equivalent of the agent taking 20 actions.
    for _ in range(50):  # This for loop should never actually fully complete.
        if tap001.current_kill_chain_stage == BaseKillChain.SUCCEEDED:
            break
        env.step(0)

    # Catches if the above for loop fully completes.
    # This test uses a probability of 1 for all stages and a variance of 2 timesteps
    # Thus the for loop above should never fail.
    # If this occurs then there is an error somewhere in either:
    # 1. The TAP Logic
    # 2. Failing Agent Actions are causing the TAP to fail. (See tap_return_handler).
    if tap001.current_kill_chain_stage != BaseKillChain.SUCCEEDED:
        pytest.fail("Attacker Never Reached SUCCEEDED - Please evaluate current TAP Logic.")

    # Stepping twice for the succeeded logic to kick in:
    env.step(0)
    env.step(0)
    env.step(0)
    env.step(0)

    assert tap001.current_kill_chain_stage.name == MobileMalwareKillChain.DOWNLOAD.name
    assert tap001.next_kill_chain_stage.name == MobileMalwareKillChain.INSTALL.name


def test_tap001_repeating_kill_chain_stages():
    """Tests to check that tap001 repeats it's kill chain after failing a kill chain stage."""
    env = uc7_tap001_env(
        repeat_kill_chain=True,
        repeat_kill_chain_stages=True,
        payload_probability=1,
        propagate_probability=0,
        # Probability 0 = Will never be able to perform the access stage and progress to Manipulation.
    )
    tap001: TAP001 = env.game.agents["attacker"]
    env.step(0)  # Skipping not started
    env.step(0)  # Successful on the first stage
    assert tap001.current_kill_chain_stage.name == MobileMalwareKillChain.DOWNLOAD.name
    assert tap001.next_kill_chain_stage.name == MobileMalwareKillChain.INSTALL.name
    env.step(0)  # Successful progression to the second stage
    env.step(0)
    env.step(0)
    env.step(0)
    assert tap001.current_kill_chain_stage.name == MobileMalwareKillChain.INSTALL.name
    assert tap001.next_kill_chain_stage.name == MobileMalwareKillChain.ACTIVATE.name
    env.step(0)  # Successful progression to the third stage
    env.step(0)
    assert tap001.current_kill_chain_stage.name == MobileMalwareKillChain.ACTIVATE.name
    assert tap001.next_kill_chain_stage.name == MobileMalwareKillChain.PROPAGATE.name
    env.step(0)  # Successful progression to the Fourth stage
    env.step(0)
    env.step(0)
    env.step(0)
    assert tap001.current_kill_chain_stage.name == MobileMalwareKillChain.PROPAGATE.name
    assert tap001.next_kill_chain_stage.name == MobileMalwareKillChain.COMMAND_AND_CONTROL.name
    env.step(0)  # FAILURE -- Unsuccessful progression to the Fourth stage
    env.step(0)
    assert tap001.current_kill_chain_stage.name == MobileMalwareKillChain.PROPAGATE.name
    assert tap001.next_kill_chain_stage.name == MobileMalwareKillChain.COMMAND_AND_CONTROL.name
    assert tap001.current_stage_progress == KillChainStageProgress.PENDING
