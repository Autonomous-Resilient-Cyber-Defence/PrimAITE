from pathlib import Path
from typing import Dict, Final, Union

import yaml

from primaite import getLogger, PRIMAITE_PATHS

_LOGGER = getLogger(__name__)

_EXAMPLE_CFG: Final[Path] = PRIMAITE_PATHS.user_config_path / "example_config"


def load(file_path: Union[str, Path]) -> Dict:
    """
    Read a YAML file and return the contents as a dictionary.

    :param file_path: Path to the YAML file.
    :type file_path: Union[str, Path]
    :return: Config dictionary
    :rtype: Dict
    """
    if not isinstance(file_path, Path):
        file_path = Path(file_path)
    if not file_path.exists():
        _LOGGER.error(f"File does not exist: {file_path}")
        raise FileNotFoundError(f"File does not exist: {file_path}")
    with open(file_path, "r") as file:
        config = yaml.safe_load(file)
        _LOGGER.debug(f"Loaded config from {file_path}")
    return config


def data_manipulation_config_path() -> Path:
    """
    Get the path to the example config.

    :return: Path to the example config.
    :rtype: Path
    """
    path = _EXAMPLE_CFG / "data_manipulation.yaml"
    if not path.exists():
        msg = f"Example config does not exist: {path}. Have you run `primaite setup`?"
        _LOGGER.error(msg)
        raise FileNotFoundError(msg)
    return path
