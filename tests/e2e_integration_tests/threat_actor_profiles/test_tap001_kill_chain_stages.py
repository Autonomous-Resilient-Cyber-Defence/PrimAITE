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

# Defining constants.

START_STEP = 1  # The starting step of the agent.
FREQUENCY = 2  # The frequency of kill chain stage progression (E.g it's next attempt at "attacking").
VARIANCE = 0  # The timestep variance between kill chain progression (E.g Next timestep = Frequency +/- variance)
REPEAT_KILL_CHAIN = False  # Should the TAP repeat the kill chain after success/failure?
REPEAT_KILL_CHAIN_STAGES = False  # Should the TAP restart from it's previous stage on failure?
KILL_CHAIN_PROBABILITY = 1  # Blank probability for agent 'success'
DATA_EXFIL = True  # Data exfiltration on the payload stage is enabled.
ATTACK_AGENT_INDEX = 32


def uc7_tap001_env() -> PrimaiteGymEnv:
    """Setups the UC7 tap001 Game with the start_step & frequency set to 1 with probabilities set to 1 as well"""
    with open(_EXAMPLE_CFG / "uc7_config.yaml", mode="r") as uc7_config:
        cfg = yaml.safe_load(uc7_config)
        cfg["io_settings"]["save_sys_logs"] = False
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["start_step"] = START_STEP
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["frequency"] = FREQUENCY
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["variance"] = VARIANCE
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["repeat_kill_chain"] = REPEAT_KILL_CHAIN_STAGES
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["repeat_kill_chain_stages"] = REPEAT_KILL_CHAIN_STAGES
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["kill_chain"]["PAYLOAD"][
            "probability"
        ] = KILL_CHAIN_PROBABILITY
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["kill_chain"]["PROPAGATE"][
            "probability"
        ] = KILL_CHAIN_PROBABILITY
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["kill_chain"]["PAYLOAD"]["exfiltrate"] = DATA_EXFIL
    env = PrimaiteGymEnv(env_config=cfg)
    return env


def test_tap001_kill_chain_stage_DOWNLOAD():
    """Tests that the DOWNLOAD Mobile Malware step works as expected and the expected impacts are made in the simulation."""

    # Instantiating the relevant simulation/game objects:
    env = uc7_tap001_env()
    tap001: TAP001 = env.game.agents["attacker"]
    starting_host = env.game.simulation.network.get_node_by_hostname(tap001.starting_node)
    assert tap001.current_kill_chain_stage == BaseKillChain.NOT_STARTED

    # Frequency is set to two steps so we need to step through the environment a couple of times
    # In order for TAP001 to move onto the next kill chain stage.
    env.step(0)
    env.step(0)

    env.step(0)
    env.step(0)

    assert tap001.current_kill_chain_stage.name == MobileMalwareKillChain.DOWNLOAD.name
    assert tap001.next_kill_chain_stage.name == MobileMalwareKillChain.INSTALL.name
    assert tap001.current_stage_progress == KillChainStageProgress.IN_PROGRESS

    # Creating the "downloads" folder
    env.step(0)
    env.step(0)

    assert starting_host.software_manager.file_system.get_folder(folder_name="downloads")
    assert starting_host.software_manager.file_system.get_file(folder_name="downloads", file_name="malware_dropper.ps1")

    # Testing that the num_file_increase works

    assert starting_host.file_system.num_file_creations == 1


def test_tap001_kill_chain_stage_INSTALL():
    """Tests that the INSTALL Mobile Malware step works as expected and the expected impacts are made in the simulation."""
    env = uc7_tap001_env()
    tap001: TAP001 = env.game.agents["attacker"]
    # The tap001's Starting Client:
    starting_host = env.game.simulation.network.get_node_by_hostname(tap001.starting_node)

    # Skipping directly to the activate stage
    for _ in range(6):
        env.step(0)

    # Testing that tap001 Enters into the expected kill chain stages
    assert tap001.current_kill_chain_stage.name == MobileMalwareKillChain.INSTALL.name
    assert tap001.next_kill_chain_stage.name == MobileMalwareKillChain.ACTIVATE.name

    env.step(0)  # Allows the agent action to resolve.
    env.step(0)

    ransomware_dropper_file = starting_host.software_manager.file_system.get_file(
        folder_name="downloads", file_name="malware_dropper.ps1"
    )
    assert ransomware_dropper_file.num_access == 1


def test_tap001_kill_chain_stage_ACTIVATE():
    """Tests that the ACTIVATE Mobile Malware step works as expected and the current impacts are made in the simulation."""
    env = uc7_tap001_env()
    tap001: TAP001 = env.game.agents["attacker"]
    # The tap001's Starting Client:
    starting_host = env.game.simulation.network.get_node_by_hostname(tap001.starting_node)

    # Skipping directly to the activate stage
    for _ in range(8):
        env.step(0)

    assert tap001.current_kill_chain_stage.name == MobileMalwareKillChain.ACTIVATE.name
    assert tap001.next_kill_chain_stage.name == MobileMalwareKillChain.PROPAGATE.name

    # Installing ransomware-script Application
    env.step(0)
    env.step(0)

    # Installing NMAP Application
    env.step(0)
    env.step(0)

    # These asserts will fail if the applications are not present in the software_manager
    assert starting_host.software_manager.software["ransomware-script"]
    assert starting_host.software_manager.software["nmap"]


def test_tap001_kill_chain_stage_PROPAGATE():
    """Tests that the ACTIVATE Mobile Malware step works as expected and the current impacts are made in the simulation."""
    env = uc7_tap001_env()
    tap001: TAP001 = env.game.agents["attacker"]

    for _ in range(12):
        env.step(0)

    assert tap001.current_kill_chain_stage.name == MobileMalwareKillChain.PROPAGATE.name
    assert tap001.next_kill_chain_stage.name == MobileMalwareKillChain.COMMAND_AND_CONTROL.name

    # Specific Stage by Stage Propagate Testing is done in test_tap001_propagate.
    fail_safe_var = 0
    while tap001.current_kill_chain_stage.name == MobileMalwareKillChain.PROPAGATE:
        env.step(0)
        assert tap001.current_stage_progress == KillChainStageProgress.IN_PROGRESS
        fail_safe_var += 1
        if fail_safe_var == 100:
            pytest.fail("Fail Safe Variable was hit! -- Propagate step is running indefinitely")


def test_tap001_kill_chain_stage_COMMAND_AND_CONTROL():
    """Tests that the Command And Control Mobile Malware step works as expected and the current impacts are made in the simulation."""
    env = uc7_tap001_env()
    tap001: TAP001 = env.game.agents["attacker"]
    fail_safe_var = 0

    for _ in range(28):
        env.step(0)

    assert tap001.current_kill_chain_stage.name == MobileMalwareKillChain.COMMAND_AND_CONTROL.name
    assert tap001.next_kill_chain_stage.name == MobileMalwareKillChain.PAYLOAD.name

    while tap001.current_kill_chain_stage == MobileMalwareKillChain.COMMAND_AND_CONTROL:
        env.step(0)
        fail_safe_var += 1
        env.game.simulation.network.airspace.show()
        if fail_safe_var == 100:
            pytest.fail(reason="Fail Safe Variable was hit! -- Propagate step is running indefinitely")

    starting_host = env.game.simulation.network.get_node_by_hostname(tap001.starting_node)

    c2_beacon: C2Beacon = starting_host.software_manager.software["c2-beacon"]

    assert c2_beacon.c2_connection_active is True


def test_tap001_kill_chain_stage_PAYLOAD():
    """Tests that the PAYLOAD Mobile Malware step works as expected and the current impacts are made in the simulation."""

    env = uc7_tap001_env()
    tap001: TAP001 = env.game.agents["attacker"]

    # The tap001's Target Database
    target_host = env.game.simulation.network.get_node_by_hostname("ST_DATA-PRV-SRV-DB")
    db_server_service: DatabaseService = target_host.software_manager.software.get("database-service")

    # Green agent status requests are tested within the ransomware application tests.
    # See test_ransomware_disrupts_green_agent_connection for further reference.
    assert db_server_service.db_file.health_status is FileSystemItemHealthStatus.GOOD

    fail_safe_var = 0
    while tap001.current_kill_chain_stage != MobileMalwareKillChain.PAYLOAD:
        env.step(0)
        fail_safe_var += 1
        if fail_safe_var == 100:
            pytest.fail(reason="Fail Safe Variable was hit! -- a step is running indefinitely")

    for _ in range(12):
        env.step(0)

    assert db_server_service.db_file.health_status is FileSystemItemHealthStatus.CORRUPT

    # Asserting we've managed to the database.db file onto the starting node & server
    starting_host = env.game.simulation.network.get_node_by_hostname(tap001.starting_node)
    c2_host = env.game.simulation.network.get_node_by_hostname(tap001.c2_settings["c2_server"])

    assert starting_host.file_system.access_file(folder_name="exfiltration_folder", file_name="database.db")
    assert c2_host.file_system.access_file(folder_name="exfiltration_folder", file_name="database.db")
