# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from typing import Tuple

import pytest

from primaite.game.agent.interface import ProxyAgent
from primaite.game.game import PrimaiteGame
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.host.computer import Computer


@pytest.fixture
def game_and_agent_fixture(game_and_agent):
    """Create a game with a simple agent that can be controlled by the tests."""
    game, agent = game_and_agent

    client_1: Computer = game.simulation.network.get_node_by_hostname("client_1")
    client_1.start_up_duration = 3

    return (game, agent)


def test_node_startup_shutdown(game_and_agent_fixture: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that the node can be shut down and started up."""
    game, agent = game_and_agent_fixture

    client_1 = game.simulation.network.get_node_by_hostname("client_1")

    assert client_1.operating_state == NodeOperatingState.ON

    # turn it off
    action = ("NODE_SHUTDOWN", {"node_id": 0})
    agent.store_action(action)
    game.step()

    assert client_1.operating_state == NodeOperatingState.SHUTTING_DOWN

    for i in range(client_1.shut_down_duration + 1):
        action = ("DONOTHING", {"node_id": 0})
        agent.store_action(action)
        game.step()

    assert client_1.operating_state == NodeOperatingState.OFF

    # turn it on
    action = ("NODE_STARTUP", {"node_id": 0})
    agent.store_action(action)
    game.step()

    assert client_1.operating_state == NodeOperatingState.BOOTING

    for i in range(client_1.start_up_duration + 1):
        action = ("DONOTHING", {"node_id": 0})
        agent.store_action(action)
        game.step()

    assert client_1.operating_state == NodeOperatingState.ON


def test_node_cannot_be_started_up_if_node_is_already_on(game_and_agent_fixture: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that a node cannot be started up if it is already on."""
    game, agent = game_and_agent_fixture

    client_1 = game.simulation.network.get_node_by_hostname("client_1")
    assert client_1.operating_state == NodeOperatingState.ON

    # turn it on
    action = ("NODE_STARTUP", {"node_id": 0})
    agent.store_action(action)
    game.step()

    assert client_1.operating_state == NodeOperatingState.ON


def test_node_cannot_be_shut_down_if_node_is_already_off(game_and_agent_fixture: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that a node cannot be shut down if it is already off."""
    game, agent = game_and_agent_fixture

    client_1 = game.simulation.network.get_node_by_hostname("client_1")
    client_1.power_off()

    for i in range(client_1.shut_down_duration + 1):
        action = ("DONOTHING", {"node_id": 0})
        agent.store_action(action)
        game.step()

    assert client_1.operating_state == NodeOperatingState.OFF

    # turn it ff
    action = ("NODE_SHUTDOWN", {"node_id": 0})
    agent.store_action(action)
    game.step()

    assert client_1.operating_state == NodeOperatingState.OFF
