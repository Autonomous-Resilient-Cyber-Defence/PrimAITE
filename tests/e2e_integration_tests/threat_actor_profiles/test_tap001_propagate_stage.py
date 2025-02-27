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
from primaite.simulator.file_system.file_system_item_abc import FileSystemItemHealthStatus
from primaite.simulator.system.applications.red_applications.c2.c2_beacon import C2Beacon
from primaite.simulator.system.services.database.database_service import DatabaseService

# Defining generic tap constants.

START_STEP = 1  # The starting step of the agent.
FREQUENCY = 2  # The frequency of kill chain stage progression (E.g it's next attempt at "attacking").
VARIANCE = 0  # The timestep variance between kill chain progression (E.g Next timestep = Frequency +/- variance)
REPEAT_KILL_CHAIN = False  # Should the TAP repeat the kill chain after success/failure?
REPEAT_KILL_CHAIN_STAGES = False  # Should the TAP restart from it's previous stage on failure?
KILL_CHAIN_PROBABILITY = 1  # Blank probability for agent 'success's.
ATTACK_AGENT_INDEX = 32


def uc7_tap001_env(**kwargs) -> PrimaiteGymEnv:
    """Setups the UC7 tap001 Game with the start_step & frequency set to 1 with probabilities set to 1 as well"""
    with open(_EXAMPLE_CFG / "uc7_config.yaml", mode="r") as uc7_config:
        cfg = yaml.safe_load(uc7_config)
        cfg["io_settings"]["save_sys_logs"] = False
        agent_cfg = cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]
        agent_cfg["start_step"] = START_STEP
        agent_cfg["frequency"] = FREQUENCY
        agent_cfg["variance"] = VARIANCE
        agent_cfg["repeat_kill_chain"] = REPEAT_KILL_CHAIN_STAGES
        agent_cfg["repeat_kill_chain_stages"] = REPEAT_KILL_CHAIN_STAGES
        agent_cfg["kill_chain"]["PAYLOAD"]["probability"] = KILL_CHAIN_PROBABILITY
        agent_cfg["kill_chain"]["PROPAGATE"]["probability"] = KILL_CHAIN_PROBABILITY
        agent_cfg["kill_chain"]["PROPAGATE"]["scan_attempts"] = kwargs["scan_attempts"]
        agent_cfg["kill_chain"]["PAYLOAD"]["payload"] = kwargs["payload"]
        agent_cfg["kill_chain"]["PROPAGATE"]["network_addresses"] = kwargs["network_addresses"]
        if "repeat_scan" in kwargs:
            agent_cfg["kill_chain"]["PROPAGATE"]["repeat_scan"] = kwargs["repeat_scan"]
        if "starting_nodes" in kwargs:
            agent_cfg["starting_nodes"] = kwargs["starting_nodes"]
            agent_cfg["default_starting_node"] = kwargs["starting_nodes"][0]
        if "target_ips" in kwargs:
            agent_cfg["target_ips"] = kwargs["target_ips"]
    env = PrimaiteGymEnv(env_config=cfg)
    return env


def test_tap001_kill_chain_stage_PROPAGATE_default():
    """Tests that the PROPAGATE Mobile Malware step works as expected and the current impacts are made in the simulation."""
    payload = "ENCRYPT"
    scan_attempts = 10
    network_addresses = [
        "192.168.230.0/29",
        "192.168.10.0/26",
        "192.168.20.0/30",
        "192.168.240.0/29",
        "192.168.220.0/29",
    ]
    env = uc7_tap001_env(payload=payload, scan_attempts=scan_attempts, network_addresses=network_addresses)
    tap001: TAP001 = env.game.agents["attacker"]

    # First Kill Chain Stages
    for _ in range(12):
        env.step(0)

    # Assert that we're about to enter into the propagate stage.
    assert tap001.current_kill_chain_stage.name == MobileMalwareKillChain.PROPAGATE.name
    assert tap001.next_kill_chain_stage.name == MobileMalwareKillChain.COMMAND_AND_CONTROL.name

    # Move into the propagate stage.
    while tap001.current_kill_chain_stage == MobileMalwareKillChain.PROPAGATE:
        env.step(0)

    # Assert that we've successfully moved into the command and control stage.
    assert tap001.current_kill_chain_stage.name == MobileMalwareKillChain.COMMAND_AND_CONTROL.name
    assert tap001.next_kill_chain_stage.name == MobileMalwareKillChain.PAYLOAD.name


def test_tap001_kill_chain_stage_PROPAGATE_different_starting_node():
    """Tests that the PROPAGATE Mobile Malware step works as expected and the current impacts are made in the simulation from a different starting node."""
    payload = "ENCRYPT"
    scan_attempts = 10
    network_addresses = [
        "192.168.230.0/29",
        "192.168.10.0/26",
        "192.168.20.0/30",
        "192.168.240.0/29",
        "192.168.220.0/29",
    ]
    starting_nodes = ["ST_PROJ-B-PRV-PC-2", "ST_PROJ-C-PRV-PC-3"]

    env = uc7_tap001_env(
        payload=payload, scan_attempts=scan_attempts, network_addresses=network_addresses, starting_nodes=starting_nodes
    )

    tap001: TAP001 = env.game.agents["attacker"]

    for _ in range(12):
        env.step(0)

    assert tap001.current_kill_chain_stage.name == MobileMalwareKillChain.PROPAGATE.name
    assert tap001.next_kill_chain_stage.name == MobileMalwareKillChain.COMMAND_AND_CONTROL.name

    # Specific Stage by Stage Propagate Testing is done in test_tap001_propagate.
    while tap001.current_kill_chain_stage == MobileMalwareKillChain.PROPAGATE:
        env.step(0)

    assert tap001.current_kill_chain_stage.name == MobileMalwareKillChain.COMMAND_AND_CONTROL.name
    assert tap001.next_kill_chain_stage.name == MobileMalwareKillChain.PAYLOAD.name


def test_tap001_kill_chain_stage_PROPAGATE_repeat_scan():
    """Tests that the PROPAGATE Mobile Malware step will fail when the target is unable to be located."""
    payload = "ENCRYPT"
    scan_attempts = 20
    repeat_scan = True
    network_addresses = ["192.168.1.0/24", "192.168.0.0/28", "100.64.0.0/30", "172.168.0.0/28"]
    env = uc7_tap001_env(
        payload=payload, scan_attempts=scan_attempts, network_addresses=network_addresses, repeat_scan=repeat_scan
    )
    for _ in range(12):
        env.step(0)

    tap001: TAP001 = env.game.agents["attacker"]

    while tap001.current_kill_chain_stage == MobileMalwareKillChain.PROPAGATE:
        env.step(0)

    # As the given network_address does not contain the target, we should fail because the maximum amount of scan attempts has been reached
    assert tap001.scans_complete == scan_attempts
    assert tap001.current_kill_chain_stage == MobileMalwareKillChain.FAILED
