# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
from pathlib import Path
from typing import Final

import networkx

from primaite import USERS_CONFIG_DIR, getLogger

_LOGGER = getLogger(__name__)

_EXAMPLE_LAY_DOWN: Final[Path] = USERS_CONFIG_DIR / "example_config" / "lay_down"


# class LayDownConfig:
#     network: networkx.Graph
#     POL
#     EIR
#     ACL

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
