# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from typing import Tuple

import pytest

from primaite.game.agent.interface import ProxyAgent
from primaite.game.game import PrimaiteGame
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.system.applications.application import ApplicationOperatingState
from primaite.simulator.system.applications.web_browser import WebBrowser
from primaite.simulator.system.services.service import ServiceOperatingState


@pytest.fixture
def game_and_agent_fixture(game_and_agent):
    """Create a game with a simple agent that can be controlled by the tests."""
    game, agent = game_and_agent

    client_1: Computer = game.simulation.network.get_node_by_hostname("client_1")
    client_1.start_up_duration = 3

    return (game, agent)


def test_application_cannot_perform_actions_unless_running(game_and_agent_fixture: Tuple[PrimaiteGame, ProxyAgent]):
    """Test the the request permissions prevent any actions unless application is running."""
    game, agent = game_and_agent_fixture

    client_1 = game.simulation.network.get_node_by_hostname("client_1")
    browser: WebBrowser = client_1.software_manager.software.get("web-browser")

    browser.close()
    assert browser.operating_state == ApplicationOperatingState.CLOSED

    action = ("node-application-scan", {"node_name": "client_1", "application_name": "web-browser"})
    agent.store_action(action)
    game.step()
    assert browser.operating_state == ApplicationOperatingState.CLOSED

    action = ("node-application-close", {"node_name": "client_1", "application_name": "web-browser"})
    agent.store_action(action)
    game.step()
    assert browser.operating_state == ApplicationOperatingState.CLOSED

    action = ("node-application-fix", {"node_name": "client_1", "application_name": "web-browser"})
    agent.store_action(action)
    game.step()
    assert browser.operating_state == ApplicationOperatingState.CLOSED

    action = ("node-application-execute", {"node_name": "client_1", "application_name": "web-browser"})
    agent.store_action(action)
    game.step()
    assert browser.operating_state == ApplicationOperatingState.CLOSED
