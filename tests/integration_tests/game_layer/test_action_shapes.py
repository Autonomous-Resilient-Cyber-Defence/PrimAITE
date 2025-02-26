# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from typing import Tuple

from primaite.game.agent.interface import ProxyAgent
from primaite.game.game import PrimaiteGame
from tests import TEST_ASSETS_ROOT

FIREWALL_ACTIONS_NETWORK = TEST_ASSETS_ROOT / "configs/firewall_actions_network.yaml"


def test_router_acl_add_rule_action_shape(game_and_agent: Tuple[PrimaiteGame, ProxyAgent]):
    """Test to check ROUTER_ADD_ACL_RULE has the expected action shape."""
    game, agent = game_and_agent

    # assert that the shape of the actions is correct
    router_acl_add_rule_action = agent.action_manager.actions.get("ROUTER_ACL_ADDRULE")
    assert router_acl_add_rule_action.shape.get("source_ip_id") == len(agent.action_manager.ip_address_list)
    assert router_acl_add_rule_action.shape.get("dest_ip_id") == len(agent.action_manager.ip_address_list)
    assert router_acl_add_rule_action.shape.get("source_port_id") == len(agent.action_manager.ports)
    assert router_acl_add_rule_action.shape.get("dest_port_id") == len(agent.action_manager.ports)
    assert router_acl_add_rule_action.shape.get("protocol_id") == len(agent.action_manager.protocols)
