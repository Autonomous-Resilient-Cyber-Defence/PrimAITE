from typing import Dict

import yaml

from primaite import PRIMAITE_PATHS


def get_primaite_config_dict() -> Dict:
    """Returns a dict containing the PrimAITE application config."""
    if PRIMAITE_PATHS.app_config_file_path.exists():
        with open(PRIMAITE_PATHS.app_config_file_path, "r") as file:
            return yaml.safe_load(file)
    else:
        print("PrimAITE application config was not found. Have you run [bold red]primaite setup[/bold red]?")


def is_dev_mode() -> bool:
    """Returns True if PrimAITE is currently running in developer mode."""
    config = get_primaite_config_dict()
    return config["developer_mode"]["enabled"]


def update_primaite_config(config: Dict) -> None:
    """Update the PrimAITE application config file."""
    with open(PRIMAITE_PATHS.app_config_file_path, "w") as file:
        yaml.dump(config, file)
