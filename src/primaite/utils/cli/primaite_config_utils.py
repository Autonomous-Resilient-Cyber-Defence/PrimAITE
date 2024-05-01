from typing import Dict, Optional

import yaml

from primaite import PRIMAITE_CONFIG, PRIMAITE_PATHS


def is_dev_mode() -> bool:
    """Returns True if PrimAITE is currently running in developer mode."""
    return PRIMAITE_CONFIG["developer_mode"]["enabled"]


def update_primaite_application_config(config: Optional[Dict] = None) -> None:
    """
    Update the PrimAITE application config file.

    :params: config: Leave empty so that PRIMAITE_CONFIG is used - otherwise provide the Dict
    """
    with open(PRIMAITE_PATHS.app_config_file_path, "w") as file:
        if not config:
            config = PRIMAITE_CONFIG
        yaml.dump(config, file)
