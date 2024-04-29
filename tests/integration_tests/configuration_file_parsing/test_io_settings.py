from pathlib import Path
from typing import Union

import yaml

from primaite.config.load import data_manipulation_config_path
from primaite.game.game import PrimaiteGame
from primaite.session.environment import PrimaiteGymEnv
from primaite.simulator import LogLevel
from tests import TEST_ASSETS_ROOT

BASIC_CONFIG = TEST_ASSETS_ROOT / "configs/basic_switched_network.yaml"


def load_config(config_path: Union[str, Path]) -> PrimaiteGame:
    """Returns a PrimaiteGame object which loads the contents of a given yaml path."""
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    return PrimaiteGame.from_config(cfg)


def test_io_settings():
    """Test that the io_settings are loaded correctly."""
    with open(BASIC_CONFIG, "r") as f:
        cfg = yaml.safe_load(f)
        env = PrimaiteGymEnv(env_config=cfg)

        assert env.io.settings is not None

        assert env.io.settings.sys_log_level is LogLevel.WARNING
        assert env.io.settings.save_pcap_logs
        assert env.io.settings.save_sys_logs
        assert env.io.settings.save_step_metadata is False

        assert env.io.settings.write_sys_log_to_terminal is False  # false by default
