# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from pathlib import Path
from typing import Union

import yaml

from primaite.config.load import data_manipulation_config_path
from primaite.game.game import PrimaiteGame
from tests import TEST_ASSETS_ROOT

BASIC_SWITCHED_NETWORK_CONFIG = TEST_ASSETS_ROOT / "configs/basic_switched_network.yaml"


def load_config(config_path: Union[str, Path]) -> PrimaiteGame:
    """Returns a PrimaiteGame object which loads the contents of a given yaml path."""
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    return PrimaiteGame.from_config(cfg)


def test_thresholds():
    """Test that the game options can be parsed correctly."""
    game = load_config(data_manipulation_config_path())

    assert game.options.thresholds is not None


def test_nmne_threshold():
    """Test that the NMNE thresholds are properly loaded in by observation."""
    game = load_config(BASIC_SWITCHED_NETWORK_CONFIG)

    assert game.options.thresholds["nmne"] is not None

    # get NIC observation
    nic_obs = game.agents["defender"].observation_manager.obs.components["NODES"].hosts[0].nics[0]
    assert nic_obs.low_nmne_threshold == 5
    assert nic_obs.med_nmne_threshold == 25
    assert nic_obs.high_nmne_threshold == 100


def test_file_access_threshold():
    """Test that the NMNE thresholds are properly loaded in by observation."""
    game = load_config(BASIC_SWITCHED_NETWORK_CONFIG)

    assert game.options.thresholds["file_access"] is not None

    # get file observation
    file_obs = game.agents["defender"].observation_manager.obs.components["NODES"].hosts[0].folders[0].files[0]
    assert file_obs.low_file_access_threshold == 2
    assert file_obs.med_file_access_threshold == 5
    assert file_obs.high_file_access_threshold == 10


def test_app_executions_threshold():
    """Test that the NMNE thresholds are properly loaded in by observation."""
    game = load_config(BASIC_SWITCHED_NETWORK_CONFIG)

    assert game.options.thresholds["app_executions"] is not None

    # get application observation
    app_obs = game.agents["defender"].observation_manager.obs.components["NODES"].hosts[0].applications[0]
    assert app_obs.low_app_execution_threshold == 2
    assert app_obs.med_app_execution_threshold == 3
    assert app_obs.high_app_execution_threshold == 5
