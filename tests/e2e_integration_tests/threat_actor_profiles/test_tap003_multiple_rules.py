# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from typing import Protocol

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
from primaite.simulator.network.hardware.nodes.network.router import ACLAction, Router
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.ipv4_address import IPV4Address
from primaite.utils.validation.port import PORT_LOOKUP

# Defining constants.
ATTACK_AGENT_INDEX = 32
START_STEP = 1  # The starting step of the agent.
FREQUENCY = 2  # The frequency of kill chain stage progression (E.g it's next attempt at "attacking").
VARIANCE = 0  # The timestep variance between kill chain progression (E.g Next timestep = Frequency +/- variance)
REPEAT_KILL_CHAIN = False  # Should the TAP repeat the kill chain after success/failure?
REPEAT_KILL_CHAIN_STAGES = False  # Should the TAP restart from it's previous stage on failure?
KILL_CHAIN_PROBABILITY = 1  # Blank probability for agent 'success'
RULES = [
    {
        "target_router": "ST_INTRA-PRV-RT-DR-1",
        "position": 1,
        "permission": "DENY",
        "src_ip": "192.168.220.3",
        "src_wildcard": "NONE",
        "dst_ip": "192.168.220.3",
        "dst_wildcard": "NONE",
        "src_port": "ALL",
        "dst_port": "ALL",
        "protocol_name": "ALL",
    },
    {
        "target_router": "ST_INTRA-PRV-RT-DR-2",
        "position": 5,
        "permission": "DENY",
        "src_ip": "192.168.220.3",
        "src_wildcard": "NONE",
        "dst_ip": "ALL",
        "dst_wildcard": "NONE",
        "src_port": "ALL",
        "dst_port": "ALL",
        "protocol_name": "ALL",
    },
    {
        "target_router": "ST_INTRA-PRV-RT-CR",
        "position": 6,
        "permission": "PERMIT",
        "src_ip": "192.168.220.3",
        "src_wildcard": "NONE",
        "dst_ip": "ALL",
        "dst_wildcard": "NONE",
        "src_port": "ALL",
        "dst_port": "ALL",
        "protocol_name": "ALL",
    },
    {
        "target_router": "REM-PUB-RT-DR",
        "position": 3,
        "permission": "PERMIT",
        "src_ip": "192.168.220.3",
        "src_wildcard": "0.0.0.1",
        "dst_ip": "192.168.220.3",
        "dst_wildcard": "0.0.0.1",
        "src_port": "FTP",
        "dst_port": "FTP",
        "protocol_name": "TCP",
    },
    #
]


def uc7_tap003_env(**kwargs) -> PrimaiteGymEnv:
    """Setups the UC7 TAP003 Game with the start_step & frequency set to 1 with probabilities set to 1 as well"""
    with open(_EXAMPLE_CFG / "uc7_config_tap003.yaml", mode="r") as uc7_config:
        cfg = yaml.safe_load(uc7_config)
        cfg["io_settings"]["save_sys_logs"] = False
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["start_step"] = START_STEP
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["frequency"] = FREQUENCY
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["variance"] = VARIANCE
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["repeat_kill_chain"] = kwargs["repeat_kill_chain"]
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["repeat_kill_chain_stages"] = kwargs[
            "repeat_kill_chain_stages"
        ]
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["kill_chain"]["MANIPULATION"]["probability"] = kwargs[
            "manipulation_probability"
        ]
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["kill_chain"]["ACCESS"]["probability"] = kwargs[
            "access_probability"
        ]
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["kill_chain"]["PLANNING"]["probability"] = kwargs[
            "planning_probability"
        ]
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["kill_chain"]["EXPLOIT"]["malicious_acls"] = RULES
        # Adding the new test target to TAP003's starting knowledge:
        new_target_dict = {
            "ST_INTRA-PRV-RT-DR-2": {
                "ip_address": "192.168.170.2",
                "username": "admin",
                "password": "admin",
            }
        }
        new_target_manipulation = {
            "host": "ST_INTRA-PRV-RT-DR-2",
            "ip_address": "192.168.170.2",
            "action": "change_password",
            "username": "admin",
            "new_password": "red_pass",
        }
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["kill_chain"]["PLANNING"]["starting_network_knowledge"][
            "credentials"
        ].update(new_target_dict)
        cfg["agents"][ATTACK_AGENT_INDEX]["agent_settings"]["kill_chain"]["MANIPULATION"]["account_changes"].append(
            new_target_manipulation
        )
    env = PrimaiteGymEnv(env_config=cfg)
    return env


def test_tap003_cycling_rules():
    """Tests to check that TAP003 repeats it's kill chain after success"""

    env = uc7_tap003_env(
        repeat_kill_chain=True,
        repeat_kill_chain_stages=True,
        manipulation_probability=1,
        access_probability=1,
        planning_probability=1,
    )
    tap003: TAP003 = env.game.agents["attacker"]

    def wait_until_attack():
        for _ in range(120):
            # check if the agent has executed and therefore moved onto the next rule index
            env.step(0)
            if tap003.history[-1].action == "node-send-remote-command":
                if tap003.history[-1].parameters["command"][0] == "acl":
                    return
        pytest.fail("While testing the cycling of TAP003 rules, the agent unexpectedly didn't execute its attack.")

    wait_until_attack()
    target_node: Router = env.game.simulation.network.get_node_by_hostname("ST_INTRA-PRV-RT-DR-1")
    assert (rule_0 := target_node.acl.acl[1]) is not None
    assert rule_0.action == ACLAction.DENY
    assert rule_0.protocol == None
    assert rule_0.src_ip_address == IPV4Address("192.168.220.3")
    assert rule_0.src_wildcard_mask == None
    assert rule_0.dst_ip_address == IPV4Address("192.168.220.3")
    assert rule_0.dst_wildcard_mask == None
    assert rule_0.src_port == None
    assert rule_0.dst_port == None

    target_node: Router = env.game.simulation.network.get_node_by_hostname("ST_INTRA-PRV-RT-DR-2")
    wait_until_attack()
    assert (rule_1 := target_node.acl.acl[5]) is not None
    assert rule_1.action == ACLAction.DENY
    assert rule_1.protocol == None
    assert rule_1.src_ip_address == IPV4Address("192.168.220.3")
    assert rule_1.src_wildcard_mask == None
    assert rule_1.dst_ip_address == None
    assert rule_1.dst_wildcard_mask == None
    assert rule_1.src_port == None
    assert rule_1.dst_port == None

    wait_until_attack()
    target_node: Router = env.game.simulation.network.get_node_by_hostname("ST_INTRA-PRV-RT-CR")
    assert (rule_2 := target_node.acl.acl[6]) is not None
    assert rule_2.action == ACLAction.PERMIT
    assert rule_2.protocol == None
    assert rule_2.src_ip_address == IPV4Address("192.168.220.3")
    assert rule_2.src_wildcard_mask == None  # default
    assert rule_2.dst_ip_address == None
    assert rule_2.dst_wildcard_mask == None  # default
    assert rule_2.src_port == None
    assert rule_2.dst_port == None

    wait_until_attack()
    target_node: Router = env.game.simulation.network.get_node_by_hostname("REM-PUB-RT-DR")
    assert (rule_3 := target_node.acl.acl[3]) is not None
    assert rule_3.action == ACLAction.PERMIT
    assert rule_3.protocol == PROTOCOL_LOOKUP["TCP"]
    assert rule_3.src_ip_address == IPV4Address("192.168.220.3")
    assert rule_3.src_wildcard_mask == IPV4Address("0.0.0.1")
    assert rule_3.dst_ip_address == IPV4Address("192.168.220.3")
    assert rule_3.dst_wildcard_mask == IPV4Address("0.0.0.1")
    assert rule_3.src_port == PORT_LOOKUP["FTP"]
    assert rule_3.dst_port == PORT_LOOKUP["FTP"]

    # If we've gotten this fair then we can pass the test :)
    pass
