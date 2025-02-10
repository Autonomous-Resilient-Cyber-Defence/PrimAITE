# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from pathlib import Path
from typing import Union

import yaml

from primaite.config.load import _EXAMPLE_CFG
from primaite.game.agent.scripted_agents.TAP003 import TAP003
from primaite.game.game import PrimaiteGame


def test_tap003_kill_chain_settings_load_config():
    with open(_EXAMPLE_CFG / "uc7_config_tap003.yaml", mode="r") as uc7_config:
        cfg = yaml.safe_load(uc7_config)
        cfg["agents"][32]["agent_settings"]["kill_chain"]["MANIPULATION"]["probability"] = 0.5
        cfg["agents"][32]["agent_settings"]["kill_chain"]["ACCESS"]["probability"] = 0.5
        cfg["agents"][32]["agent_settings"]["kill_chain"]["PLANNING"]["probability"] = 0.5
    game = PrimaiteGame.from_config(cfg)
    tap: TAP003 = game.agents["attacker"]
    kill_chain = tap.config.agent_settings.kill_chain
    assert kill_chain.MANIPULATION.probability == 0.5
    assert kill_chain.ACCESS.probability == 0.5
    assert kill_chain.PLANNING.probability == 0.5
