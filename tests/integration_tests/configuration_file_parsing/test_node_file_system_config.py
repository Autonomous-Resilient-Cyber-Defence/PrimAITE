# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from pathlib import Path
from typing import Union

import yaml

from primaite.game.game import PrimaiteGame
from tests import TEST_ASSETS_ROOT

BASIC_CONFIG = TEST_ASSETS_ROOT / "configs/nodes_with_initial_files.yaml"


def load_config(config_path: Union[str, Path]) -> PrimaiteGame:
    """Returns a PrimaiteGame object which loads the contents of a given yaml path."""
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    return PrimaiteGame.from_config(cfg)


def test_node_file_system_from_config():
    """Test that the appropriate files are instantiated in nodes when loaded from config."""
    game = load_config(BASIC_CONFIG)

    client_1 = game.simulation.network.get_node_by_hostname("client_1")

    assert client_1.software_manager.software.get("DatabaseService")  # database service should be installed
    assert client_1.file_system.get_file(folder_name="database", file_name="database.db")  # database files should exist

    assert client_1.software_manager.software.get("WebServer")  # web server should be installed
    assert client_1.file_system.get_file(folder_name="primaite", file_name="index.html")  # web files should exist

    client_2 = game.simulation.network.get_node_by_hostname("client_2")

    # database service should not be installed
    assert client_2.software_manager.software.get("DatabaseService") is None
    # database files should not exist
    assert client_2.file_system.get_file(folder_name="database", file_name="database.db") is None

    # web server should not be installed
    assert client_2.software_manager.software.get("WebServer") is None
    # web files should not exist
    assert client_2.file_system.get_file(folder_name="primaite", file_name="index.html") is None

    # TODO file sizes and file types
    # TODO assert that files and folders created:
    # TODO create empty folders
