# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
from pathlib import Path
from typing import Any, Dict, Final, TYPE_CHECKING, Union

import yaml

from primaite import getLogger, USERS_CONFIG_DIR

if TYPE_CHECKING:
    from logging import Logger

_LOGGER: "Logger" = getLogger(__name__)

_EXAMPLE_LAY_DOWN: Final[Path] = USERS_CONFIG_DIR / "example_config" / "lay_down"


def convert_legacy_lay_down_config_dict(legacy_config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a legacy lay down config dict to the new format.

    :param legacy_config_dict: A legacy lay down config dict.
    """
    _LOGGER.warning("Legacy lay down config conversion not yet implemented")
    return legacy_config_dict


def load(file_path: Union[str, Path], legacy_file: bool = False) -> Dict:
    """
    Read in a lay down config yaml file.

    :param file_path: The config file path.
    :param legacy_file: True if the config file is legacy format, otherwise False.
    :return: The lay down config as a dict.
    :raises ValueError: If the file_path does not exist.
    """
    if not isinstance(file_path, Path):
        file_path = Path(file_path)
    if file_path.exists():
        with open(file_path, "r") as file:
            config = yaml.safe_load(file)
            _LOGGER.debug(f"Loading lay down config file: {file_path}")
        if legacy_file:
            try:
                config = convert_legacy_lay_down_config_dict(config)
            except KeyError:
                msg = (
                    f"Failed to convert lay down config file {file_path} "
                    f"from legacy format. Attempting to use file as is."
                )
                _LOGGER.error(msg)
        return config
    msg = f"Cannot load the lay down config as it does not exist: {file_path}"
    _LOGGER.error(msg)
    raise ValueError(msg)


def ddos_basic_one_config_path() -> Path:
    """
    The path to the example lay_down_config_1_DDOS_basic.yaml file.

    :return: The file path.
    """
    path = _EXAMPLE_LAY_DOWN / "lay_down_config_1_DDOS_basic.yaml"
    if not path.exists():
        msg = "Example config not found. Please run 'primaite setup'"
        _LOGGER.critical(msg)
        raise FileNotFoundError(msg)

    return path


def ddos_basic_two_config_path() -> Path:
    """
    The path to the example lay_down_config_2_DDOS_basic.yaml file.

    :return: The file path.
    """
    path = _EXAMPLE_LAY_DOWN / "lay_down_config_2_DDOS_basic.yaml"
    if not path.exists():
        msg = "Example config not found. Please run 'primaite setup'"
        _LOGGER.critical(msg)
        raise FileNotFoundError(msg)

    return path


def dos_very_basic_config_path() -> Path:
    """
    The path to the example lay_down_config_3_DOS_very_basic.yaml file.

    :return: The file path.
    """
    path = _EXAMPLE_LAY_DOWN / "lay_down_config_3_DOS_very_basic.yaml"
    if not path.exists():
        msg = "Example config not found. Please run 'primaite setup'"
        _LOGGER.critical(msg)
        raise FileNotFoundError(msg)

    return path


def data_manipulation_config_path() -> Path:
    """
    The path to the example lay_down_config_5_data_manipulation.yaml file.

    :return: The file path.
    """
    path = _EXAMPLE_LAY_DOWN / "lay_down_config_5_data_manipulation.yaml"
    if not path.exists():
        msg = "Example config not found. Please run 'primaite setup'"
        _LOGGER.critical(msg)
        raise FileNotFoundError(msg)

    return path
