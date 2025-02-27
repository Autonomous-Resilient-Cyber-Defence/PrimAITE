# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from typing import Tuple

import pytest

from primaite.game.agent.interface import ProxyAgent
from primaite.game.game import PrimaiteGame
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.system.services.service import ServiceOperatingState


@pytest.fixture
def game_and_agent_fixture(game_and_agent):
    """Create a game with a simple agent that can be controlled by the tests."""
    game, agent = game_and_agent

    client_1: Computer = game.simulation.network.get_node_by_hostname("client_1")
    client_1.start_up_duration = 3

    return (game, agent)


def test_service_start(game_and_agent_fixture: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that the validator makes sure that the service is stopped before starting the service."""
    game, agent = game_and_agent_fixture

    server_1: Server = game.simulation.network.get_node_by_hostname("server_1")
    dns_server = server_1.software_manager.software.get("dns-server")

    dns_server.pause()
    assert dns_server.operating_state == ServiceOperatingState.PAUSED

    action = ("node-service-start", {"node_name": "server_1", "service_name": "dns-server"})
    agent.store_action(action)
    game.step()
    assert dns_server.operating_state == ServiceOperatingState.PAUSED

    dns_server.stop()

    assert dns_server.operating_state == ServiceOperatingState.STOPPED

    action = ("node-service-start", {"node_name": "server_1", "service_name": "dns-server"})
    agent.store_action(action)
    game.step()

    assert dns_server.operating_state == ServiceOperatingState.RUNNING


def test_service_resume(game_and_agent_fixture: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that the validator checks if the service is paused before resuming."""
    game, agent = game_and_agent_fixture

    server_1: Server = game.simulation.network.get_node_by_hostname("server_1")
    dns_server = server_1.software_manager.software.get("dns-server")

    action = ("node-service-resume", {"node_name": "server_1", "service_name": "dns-server"})
    agent.store_action(action)
    game.step()
    assert dns_server.operating_state == ServiceOperatingState.RUNNING

    dns_server.pause()

    assert dns_server.operating_state == ServiceOperatingState.PAUSED

    action = ("node-service-resume", {"node_name": "server_1", "service_name": "dns-server"})
    agent.store_action(action)
    game.step()

    assert dns_server.operating_state == ServiceOperatingState.RUNNING


def test_service_cannot_perform_actions_unless_running(game_and_agent_fixture: Tuple[PrimaiteGame, ProxyAgent]):
    """Test to make sure that the service cannot perform certain actions while not running."""
    game, agent = game_and_agent_fixture

    server_1: Server = game.simulation.network.get_node_by_hostname("server_1")
    dns_server = server_1.software_manager.software.get("dns-server")

    dns_server.stop()
    assert dns_server.operating_state == ServiceOperatingState.STOPPED

    action = ("node-service-scan", {"node_name": "server_1", "service_name": "dns-server"})
    agent.store_action(action)
    game.step()
    assert dns_server.operating_state == ServiceOperatingState.STOPPED

    action = ("node-service-pause", {"node_name": "server_1", "service_name": "dns-server"})
    agent.store_action(action)
    game.step()
    assert dns_server.operating_state == ServiceOperatingState.STOPPED

    action = ("node-service-resume", {"node_name": "server_1", "service_name": "dns-server"})
    agent.store_action(action)
    game.step()
    assert dns_server.operating_state == ServiceOperatingState.STOPPED

    action = ("node-service-restart", {"node_name": "server_1", "service_name": "dns-server"})
    agent.store_action(action)
    game.step()
    assert dns_server.operating_state == ServiceOperatingState.STOPPED

    action = ("node-service-fix", {"node_name": "server_1", "service_name": "dns-server"})
    agent.store_action(action)
    game.step()
    assert dns_server.operating_state == ServiceOperatingState.STOPPED
