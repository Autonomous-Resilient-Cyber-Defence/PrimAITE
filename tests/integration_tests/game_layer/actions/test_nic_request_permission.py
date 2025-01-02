# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from typing import Tuple

import pytest

from primaite.game.agent.interface import ProxyAgent
from primaite.game.game import PrimaiteGame
from primaite.simulator.network.hardware.nodes.host.computer import Computer


@pytest.fixture
def game_and_agent_fixture(game_and_agent):
    """Create a game with a simple agent that can be controlled by the tests."""
    game, agent = game_and_agent

    client_1: Computer = game.simulation.network.get_node_by_hostname("client_1")
    client_1.start_up_duration = 3

    return (game, agent)


def test_nic_cannot_be_turned_off_if_not_on(game_and_agent_fixture: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that a NIC cannot be disabled if it is not enabled."""
    game, agent = game_and_agent_fixture

    client_1 = game.simulation.network.get_node_by_hostname("client_1")
    nic = client_1.network_interface[1]
    nic.disable()
    assert nic.enabled is False

    action = (
        "HOST_NIC_DISABLE",
        {
            "node_id": 0,  # client_1
            "nic_id": 0,  # the only nic (eth-1)
        },
    )
    agent.store_action(action)
    game.step()

    assert nic.enabled is False


def test_nic_cannot_be_turned_on_if_already_on(game_and_agent_fixture: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that a NIC cannot be enabled if it is already enabled."""
    game, agent = game_and_agent_fixture

    client_1 = game.simulation.network.get_node_by_hostname("client_1")
    nic = client_1.network_interface[1]
    assert nic.enabled

    action = (
        "HOST_NIC_ENABLE",
        {
            "node_id": 0,  # client_1
            "nic_id": 0,  # the only nic (eth-1)
        },
    )
    agent.store_action(action)
    game.step()

    assert nic.enabled


def test_that_a_nic_can_be_enabled_and_disabled(game_and_agent_fixture: Tuple[PrimaiteGame, ProxyAgent]):
    """Tests that a NIC can be enabled and disabled."""
    game, agent = game_and_agent_fixture

    client_1 = game.simulation.network.get_node_by_hostname("client_1")
    nic = client_1.network_interface[1]
    assert nic.enabled

    action = (
        "HOST_NIC_DISABLE",
        {
            "node_id": 0,  # client_1
            "nic_id": 0,  # the only nic (eth-1)
        },
    )
    agent.store_action(action)
    game.step()

    assert nic.enabled is False

    action = (
        "HOST_NIC_ENABLE",
        {
            "node_id": 0,  # client_1
            "nic_id": 0,  # the only nic (eth-1)
        },
    )
    agent.store_action(action)
    game.step()

    assert nic.enabled
