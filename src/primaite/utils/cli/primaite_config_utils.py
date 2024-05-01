import yaml

from primaite import PRIMAITE_CONFIG, PRIMAITE_PATHS


def is_dev_mode() -> bool:
    """Returns True if PrimAITE is currently running in developer mode."""
    return PRIMAITE_CONFIG["developer_mode"]["enabled"]


def update_primaite_application_config() -> None:
    """Update the PrimAITE application config file."""
    with open(PRIMAITE_PATHS.app_config_file_path, "w") as file:
        yaml.dump(PRIMAITE_CONFIG, file)
