# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
import uuid
from typing import Tuple

import pytest

from primaite.game.agent.scripted_agents.interface import ProxyAgent
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


def test_create_file(game_and_agent_fixture: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that the validator allows a files to be created."""
    game, agent = game_and_agent_fixture

    client_1 = game.simulation.network.get_node_by_hostname("client_1")

    random_folder = str(uuid.uuid4())
    random_file = str(uuid.uuid4())

    assert client_1.file_system.get_file(folder_name=random_folder, file_name=random_file) is None

    action = (
        "NODE_FILE_CREATE",
        {"node_id": 0, "folder_name": random_folder, "file_name": random_file},
    )
    agent.store_action(action)
    game.step()

    assert client_1.file_system.get_file(folder_name=random_folder, file_name=random_file) is not None


def test_file_delete_action(game_and_agent_fixture: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that the validator allows a file to be deleted."""
    game, agent = game_and_agent_fixture

    client_1 = game.simulation.network.get_node_by_hostname("client_1")
    file = client_1.file_system.get_file(folder_name="downloads", file_name="cat.png")
    assert file.deleted is False

    action = (
        "NODE_FILE_DELETE",
        {"node_id": 0, "folder_id": 0, "file_id": 0},
    )
    agent.store_action(action)
    game.step()

    assert file.deleted


def test_file_scan_action(game_and_agent_fixture: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that the validator allows a file to be scanned."""
    game, agent = game_and_agent_fixture

    client_1 = game.simulation.network.get_node_by_hostname("client_1")
    file = client_1.file_system.get_file(folder_name="downloads", file_name="cat.png")

    file.corrupt()
    assert file.health_status == FileSystemItemHealthStatus.CORRUPT
    assert file.visible_health_status == FileSystemItemHealthStatus.GOOD

    action = (
        "NODE_FILE_SCAN",
        {"node_id": 0, "folder_id": 0, "file_id": 0},
    )
    agent.store_action(action)
    game.step()

    assert file.health_status == FileSystemItemHealthStatus.CORRUPT
    assert file.visible_health_status == FileSystemItemHealthStatus.CORRUPT


def test_file_repair_action(game_and_agent_fixture: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that the validator allows a folder to be created."""
    game, agent = game_and_agent_fixture

    client_1 = game.simulation.network.get_node_by_hostname("client_1")
    file = client_1.file_system.get_file(folder_name="downloads", file_name="cat.png")

    file.corrupt()
    assert file.health_status == FileSystemItemHealthStatus.CORRUPT

    action = (
        "NODE_FILE_REPAIR",
        {"node_id": 0, "folder_id": 0, "file_id": 0},
    )
    agent.store_action(action)
    game.step()

    assert file.health_status == FileSystemItemHealthStatus.GOOD


def test_file_restore_action(game_and_agent_fixture: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that the validator allows a file to be restored."""
    game, agent = game_and_agent_fixture

    client_1 = game.simulation.network.get_node_by_hostname("client_1")
    file = client_1.file_system.get_file(folder_name="downloads", file_name="cat.png")

    file.corrupt()
    assert file.health_status == FileSystemItemHealthStatus.CORRUPT

    action = (
        "NODE_FILE_RESTORE",
        {"node_id": 0, "folder_id": 0, "file_id": 0},
    )
    agent.store_action(action)
    game.step()

    assert file.health_status == FileSystemItemHealthStatus.GOOD


def test_file_corrupt_action(game_and_agent_fixture: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that the validator allows a file to be corrupted."""
    game, agent = game_and_agent_fixture

    client_1 = game.simulation.network.get_node_by_hostname("client_1")
    file = client_1.file_system.get_file(folder_name="downloads", file_name="cat.png")

    assert file.health_status == FileSystemItemHealthStatus.GOOD

    action = (
        "NODE_FILE_CORRUPT",
        {"node_id": 0, "folder_id": 0, "file_id": 0},
    )
    agent.store_action(action)
    game.step()

    assert file.health_status == FileSystemItemHealthStatus.CORRUPT


def test_file_access_action(game_and_agent_fixture: Tuple[PrimaiteGame, ProxyAgent]):
    """Test that the validator allows a file to be accessed."""
    game, agent = game_and_agent_fixture

    client_1 = game.simulation.network.get_node_by_hostname("client_1")
    file = client_1.file_system.get_file(folder_name="downloads", file_name="cat.png")
    assert file.num_access == 0

    action = (
        "NODE_FILE_ACCESS",
        {"node_id": 0, "folder_name": file.folder_name, "file_name": file.name},
    )
    agent.store_action(action)
    game.step()

    assert file.num_access == 1
