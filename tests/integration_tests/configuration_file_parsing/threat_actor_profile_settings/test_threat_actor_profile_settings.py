# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from pathlib import Path
from typing import Union

import yaml

from primaite.config.load import _EXAMPLE_CFG
from primaite.game.agent.scripted_agents.TAP003 import TAP003
from primaite.game.game import PrimaiteGame


def test_threat_actor_profile_load_config():
    """Test to check that threat actor profiles are able to be loaded."""
    with open(_EXAMPLE_CFG / "uc7_config_tap003.yaml", mode="r") as uc7_config:
        cfg = yaml.safe_load(uc7_config)

    game = PrimaiteGame.from_config(cfg)
    # tap003 is found and loaded TODO: Once tuple digestion is implemented, change to hardcoded 'tap003' test.
    assert "attacker" in game.agents
    assert isinstance(game.agents["attacker"], TAP003)
    agent: TAP003 = game.agents["attacker"]
    assert agent.config.agent_settings.start_step == 1
    assert agent.config.agent_settings.frequency == 3
    assert agent.config.agent_settings.variance == 0
    assert not agent.config.agent_settings.repeat_kill_chain
    assert agent.config.agent_settings.repeat_kill_chain_stages
    assert agent.config.agent_settings.default_starting_node == "ST-PROJ-A-PRV-PC-1"
    assert not agent.config.agent_settings.starting_nodes
    assert agent.config.agent_settings.kill_chain.PLANNING.probability == 1
    assert len(agent.config.agent_settings.kill_chain.PLANNING.starting_network_knowledge["credentials"]) == 6
    assert agent.config.agent_settings.kill_chain.ACCESS.probability == 1
    assert agent.config.agent_settings.kill_chain.MANIPULATION.probability == 1
    assert len(agent.config.agent_settings.kill_chain.MANIPULATION.account_changes) == 3
    assert agent.config.agent_settings.kill_chain.EXPLOIT.probability == 1
    assert len(agent.config.agent_settings.kill_chain.EXPLOIT.malicious_acls) == 3
