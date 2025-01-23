# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
import uuid
from typing import Tuple

import pytest

from primaite.game.agent.interface import ProxyAgent
from primaite.game.game import PrimaiteGame
from primaite.simulator.file_system.file_system_item_abc import FileSystemItemHealthStatus
from primaite.simulator.network.hardware.nodes.host.computer import Computer


@pytest.fixture
def game_and_agent_fixture(game_and_agent):
    """Create a game with a simple agent that can be controlled by the tests."""
    game, agent = game_and_agent

    client_1: Computer = game.simulation.network.get_node_by_hostname("client_1")
    client_1.start_up_duration = 3

    return (game, agent)


def test_create_folder(game_and_agent_fixture: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that the validator allows a folder to be created."""
    game, agent = game_and_agent_fixture

    client_1 = game.simulation.network.get_node_by_hostname("client_1")

    random_folder = str(uuid.uuid4())

    assert client_1.file_system.get_folder(folder_name=random_folder) is None

    action = (
        "node_folder_create",
        {
            "node_name": "client_1",
            "folder_name": random_folder,
        },
    )
    agent.store_action(action)
    game.step()

    assert client_1.file_system.get_folder(folder_name=random_folder) is not None


def test_folder_scan_action(game_and_agent_fixture: Tuple[PrimaiteGame, ProxyAgent]):
    """Test to make sure that the validator checks if the folder exists before scanning."""
    game, agent = game_and_agent_fixture

    client_1 = game.simulation.network.get_node_by_hostname("client_1")

    folder = client_1.file_system.get_folder(folder_name="downloads")
    assert folder.health_status == FileSystemItemHealthStatus.GOOD
    assert folder.visible_health_status == FileSystemItemHealthStatus.NONE

    folder.corrupt()

    assert folder.health_status == FileSystemItemHealthStatus.CORRUPT
    assert folder.visible_health_status == FileSystemItemHealthStatus.NONE

    action = (
        "node_folder_scan",
        {
            "node_name": "client_1",  # client_1,
            "folder_name": "downloads",  # downloads
        },
    )
    agent.store_action(action)
    game.step()

    for i in range(folder.scan_duration + 1):
        game.step()

    assert folder.health_status == FileSystemItemHealthStatus.CORRUPT
    assert folder.visible_health_status == FileSystemItemHealthStatus.CORRUPT


def test_folder_repair_action(game_and_agent_fixture: Tuple[PrimaiteGame, ProxyAgent]):
    """Test to make sure that the validator checks if the folder exists before repairing."""
    game, agent = game_and_agent_fixture

    client_1 = game.simulation.network.get_node_by_hostname("client_1")

    folder = client_1.file_system.get_folder(folder_name="downloads")
    folder.corrupt()
    assert folder.health_status == FileSystemItemHealthStatus.CORRUPT

    action = (
        "node_folder_repair",
        {
            "node_name": "client_1",  # client_1,
            "folder_name": "downloads",  # downloads
        },
    )
    agent.store_action(action)
    game.step()

    assert folder.health_status == FileSystemItemHealthStatus.GOOD


def test_folder_restore_action(game_and_agent_fixture: Tuple[PrimaiteGame, ProxyAgent]):
    """Test to make sure that the validator checks if the folder exists before restoring."""
    game, agent = game_and_agent_fixture

    client_1 = game.simulation.network.get_node_by_hostname("client_1")

    folder = client_1.file_system.get_folder(folder_name="downloads")
    folder.corrupt()

    assert folder.health_status == FileSystemItemHealthStatus.CORRUPT

    action = (
        "node_folder_restore",
        {
            "node_name": "client_1",  # client_1,
            "folder_name": "downloads",  # downloads
        },
    )
    agent.store_action(action)
    game.step()

    assert folder.health_status == FileSystemItemHealthStatus.RESTORING
