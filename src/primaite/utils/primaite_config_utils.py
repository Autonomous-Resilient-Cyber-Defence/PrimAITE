import yaml

from primaite import PRIMAITE_PATHS


def is_dev_mode() -> bool:
    """Returns True if PrimAITE is currently running in developer mode."""
    if PRIMAITE_PATHS.app_config_file_path.exists():
        with open(PRIMAITE_PATHS.app_config_file_path, "r") as file:
            primaite_config = yaml.safe_load(file)
            return primaite_config["developer_mode"]
