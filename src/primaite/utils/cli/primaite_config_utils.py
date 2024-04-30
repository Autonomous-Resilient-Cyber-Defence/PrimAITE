from pathlib import Path
from typing import Dict, Optional

import yaml

from primaite import PRIMAITE_PATHS


def get_primaite_config_dict(config_path: Optional[Path] = None) -> Dict:
    """
    Returns a dict containing the PrimAITE application config.

    :param: config_path: takes in a path object - leave empty to use the default app config path
    """
    err_msg = "PrimAITE application config could not be loaded."

    if config_path is None:
        config_path = PRIMAITE_PATHS.app_config_file_path
        err_msg = "PrimAITE application config was not found. Have you run `primaite setup`?"

    if config_path.exists():
        with open(config_path, "r") as file:
            return yaml.safe_load(file)
    else:
        print(err_msg)


def is_dev_mode() -> bool:
    """Returns True if PrimAITE is currently running in developer mode."""
    config = get_primaite_config_dict()
    return config["developer_mode"]["enabled"]


def update_primaite_config(config: Dict) -> None:
    """Update the PrimAITE application config file."""
    with open(PRIMAITE_PATHS.app_config_file_path, "w") as file:
        yaml.dump(config, file)
