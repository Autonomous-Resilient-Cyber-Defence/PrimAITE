from pathlib import Path
from typing import Union

import yaml

from primaite.game.game import PrimaiteGame
from tests import TEST_ASSETS_ROOT

BASIC_CONFIG = TEST_ASSETS_ROOT / "configs/basic_switched_network.yaml"

DMZ_NETWORK = TEST_ASSETS_ROOT / "configs/dmz_network.yaml"


def load_config(config_path: Union[str, Path]) -> PrimaiteGame:
    """Returns a PrimaiteGame object which loads the contents of a given yaml path."""
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    return PrimaiteGame.from_config(cfg)
